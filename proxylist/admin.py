from django.contrib import admin
from django.contrib.auth.models import Group
from django.db import IntegrityError
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import DateRangeFilter

from proxylist.models import Proxy, Subscription, BlackListHost
from proxylist.proxy import update_proxy_status


class ProxyResource(resources.ModelResource):
    class Meta:
        model = Proxy


@admin.register(Proxy)
class ProxyAdmin(ImportExportModelAdmin):
    def update_status(modeladmin, request, queryset):
        for proxy in queryset:
            update_proxy_status(proxy)
            try:
                proxy.save()
            except IntegrityError:
                # This means the proxy is either a duplicate or no longer valid
                proxy.delete()

    def quality(self, obj):
        if obj.times_checked > 0:
            return obj.times_check_succeeded * 100 / obj.times_checked
        else:
            return 0

    list_display = (
        "url",
        "location_country",
        "is_active",
        "last_checked",
        "last_active",
        "quality",
    )
    fields = ["url"]
    actions = [
        update_status,
    ]
    list_filter = (
        "is_active",
        "location_country",
        ("last_active", DateRangeFilter),
    )
    search_fields = [
        "url",
    ]
    resource_class = ProxyResource


class SubscriptionResource(resources.ModelResource):
    class Meta:
        model = Subscription


@admin.register(Subscription)
class SubscriptionAdmin(ImportExportModelAdmin):
    resource_class = SubscriptionResource

    list_display = (
        "url",
        "kind",
        "enabled",
        "alive",
        "alive_timestamp",
        "error_message",
    )
    fields = ["url", "kind", "enabled"]


@admin.register(BlackListHost)
class BlackListHostAdmin(admin.ModelAdmin):
    list_display = ("host",)
    search_fields = ["host"]


admin.site.unregister(Group)
