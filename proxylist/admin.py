from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Case, Count, FloatField, Value, When
from django.db.models.functions import Cast
from datetime import timedelta

from django.utils.html import format_html
from django.utils.timezone import now
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import DateRangeFilter

from proxylist.models import Proxy, Subscription, BlackListHost
from proxylist.proxy import update_proxy_status
from proxylist.tasks import (
    _collect_candidate_urls,
    _test_candidate_urls,
    save_proxies,
)
from proxylist.views import get_flag_or_empty


class ProxyResource(resources.ModelResource):
    class Meta:
        model = Proxy


@admin.register(Proxy)
class ProxyAdmin(ImportExportModelAdmin):
    @admin.action(description="Update status of selected proxies")
    def update_status(modeladmin, request, queryset):
        updated = 0
        deleted = 0
        for proxy in queryset:
            update_proxy_status(proxy)
            try:
                proxy.save()
                updated += 1
            except IntegrityError:
                # This means the proxy is either a duplicate or no longer valid
                proxy.delete()
                deleted += 1
        modeladmin.message_user(
            request,
            f"{updated} proxy(ies) updated, {deleted} removed as duplicate/invalid.",
        )

    @admin.display(description="Country", ordering="location_country")
    def country(self, obj):
        flag = get_flag_or_empty(obj.location_country_code)
        return f"{flag} {obj.location_country}".strip()

    @admin.display(description="Quality", ordering="quality")
    def quality(self, obj):
        if obj.times_checked > 0:
            ratio = obj.times_check_succeeded * 100 / obj.times_checked
        else:
            ratio = 0
        color = "green" if ratio >= 75 else "orange" if ratio >= 40 else "red"
        return format_html(
            '<span style="color: {}">{}% ({}/{})</span>',
            color,
            f"{ratio:.0f}",
            obj.times_check_succeeded,
            obj.times_checked,
        )

    @admin.display(description="Share")
    def share(self, obj):
        if obj.pk is None:
            return "Save the proxy first to generate its QR code and config."
        return format_html(
            '<div><img src="/{0}/qr" alt="QR code" '
            'style="max-width: 220px; border: 1px solid #ccc; padding: 4px" />'
            '</div><p><a href="/{0}/config">Download JSON config</a> &middot; '
            '<a href="/{0}/qr">Download QR code</a></p>',
            obj.pk,
        )

    list_display = (
        "url",
        "country",
        "port",
        "is_active",
        "last_checked",
        "last_active",
        "quality",
    )
    list_display_links = ("url",)
    readonly_fields = (
        "location",
        "location_country",
        "location_country_code",
        "ip_address",
        "port",
        "is_active",
        "last_checked",
        "last_active",
        "times_checked",
        "times_check_succeeded",
        "share",
    )
    fieldsets = (
        (None, {"fields": ("url", "share")}),
        (
            "Location",
            {"fields": ("location", "location_country", "location_country_code", "ip_address", "port")},
        ),
        (
            "Status",
            {
                "fields": (
                    "is_active",
                    "last_checked",
                    "last_active",
                    "times_checked",
                    "times_check_succeeded",
                )
            },
        ),
    )
    actions = [
        update_status,
    ]
    list_filter = (
        "is_active",
        "location_country",
        ("last_active", DateRangeFilter),
        ("last_checked", DateRangeFilter),
    )
    search_fields = [
        "url",
        "location",
        "location_country",
        "ip_address",
    ]
    date_hierarchy = "last_active"
    list_per_page = 50
    ordering = ("-last_active",)
    resource_class = ProxyResource

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            quality=Case(
                When(times_checked=0, then=Value(0.0)),
                default=Cast("times_check_succeeded", FloatField())
                * 100.0
                / Cast("times_checked", FloatField()),
                output_field=FloatField(),
            )
        )

    def changelist_view(self, request, extra_context=None):
        proxies = Proxy.objects.all()
        total = proxies.count()
        active = proxies.filter(is_active=True).count()
        top_countries = list(
            proxies.filter(is_active=True)
            .values("location_country")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        extra_context = extra_context or {}
        extra_context["proxy_summary"] = {
            "total": total,
            "active": active,
            "inactive": total - active,
            "top_countries": top_countries,
        }
        return super().changelist_view(request, extra_context=extra_context)


class SubscriptionResource(resources.ModelResource):
    class Meta:
        model = Subscription


@admin.register(Subscription)
class SubscriptionAdmin(ImportExportModelAdmin):
    resource_class = SubscriptionResource

    @admin.action(description="Poll selected subscriptions now")
    def poll_now(modeladmin, request, queryset):
        candidate_urls = _collect_candidate_urls(queryset.filter(enabled=True))
        candidate_urls -= set(Proxy.objects.values_list("url", flat=True))
        proxy_results = _test_candidate_urls(candidate_urls)
        saved, found = save_proxies(proxy_results)
        modeladmin.message_user(
            request,
            f"Polled {queryset.count()} subscription(s): "
            f"{found} new working proxy(ies) found, {saved} saved.",
        )

    list_display = (
        "url",
        "kind",
        "enabled",
        "alive",
        "alive_timestamp",
        "error_message",
    )
    fields = ["url", "kind", "enabled"]
    actions = [poll_now]
    list_filter = (
        "enabled",
        "alive",
        "kind",
        ("alive_timestamp", DateRangeFilter),
    )
    search_fields = ["url", "error_message"]
    date_hierarchy = "alive_timestamp"
    list_per_page = 50
    ordering = ("-alive_timestamp",)


@admin.register(BlackListHost)
class BlackListHostAdmin(admin.ModelAdmin):
    @admin.action(description="Delete existing proxies on selected hosts")
    def purge_matching_proxies(modeladmin, request, queryset):
        total_deleted = 0
        for blacklisted in queryset:
            deleted, _ = Proxy.objects.filter(
                url__contains=f"@{blacklisted.host}:"
            ).delete()
            total_deleted += deleted
        cache.clear()
        modeladmin.message_user(
            request,
            f"Deleted {total_deleted} proxy(ies) on {queryset.count()} blacklisted host(s).",
        )

    list_display = ("host",)
    search_fields = ["host"]
    ordering = ("host",)
    actions = [purge_matching_proxies]


admin.site.unregister(Group)


def _admin_metrics():
    proxies = Proxy.objects.all()
    total = proxies.count()
    active = proxies.filter(is_active=True).count()
    recently_active = proxies.filter(
        last_active__gte=now() - timedelta(hours=24)
    ).count()
    top_countries = list(
        proxies.filter(is_active=True)
        .values("location_country", "location_country_code")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    max_country = max((c["count"] for c in top_countries), default=0)
    for country in top_countries:
        country["flag"] = get_flag_or_empty(country["location_country_code"])
        country["pct"] = round(country["count"] * 100 / max_country) if max_country else 0

    subscriptions = Subscription.objects.all()
    subs_total = subscriptions.count()
    subs_enabled = subscriptions.filter(enabled=True).count()
    subs_broken = subscriptions.filter(enabled=True, alive=False).count()

    return {
        "proxies_total": total,
        "proxies_active": active,
        "proxies_inactive": total - active,
        "proxies_active_pct": round(active * 100 / total) if total else 0,
        "proxies_recently_active": recently_active,
        "top_countries": top_countries,
        "subs_total": subs_total,
        "subs_enabled": subs_enabled,
        "subs_broken": subs_broken,
        "blacklisted_hosts": BlackListHost.objects.count(),
    }


_original_index = admin.site.index


def _index_with_metrics(request, extra_context=None):
    extra_context = extra_context or {}
    extra_context["metrics"] = _admin_metrics()
    return _original_index(request, extra_context)


admin.site.index = _index_with_metrics
admin.site.index_template = "admin/shadowmere_index.html"
