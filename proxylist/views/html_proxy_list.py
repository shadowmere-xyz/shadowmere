from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from proxylist.models import Proxy, TaskLog


@cache_page(None)
def list_proxies(request):
    location_country_code = request.GET.get("location_country_code", "")
    country_codes = (
        Proxy.objects.filter(is_active=True)
        .order_by("location_country_code")
        .values("location_country_code", "location_country")
        .distinct()
    )
    if location_country_code != "":
        proxy_list = Proxy.objects.filter(
            location_country_code=location_country_code, is_active=True
        ).order_by("-id")
    else:
        proxy_list = Proxy.objects.filter(is_active=True).order_by("-id")

    paginator = Paginator(proxy_list, 10)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    update_status_logs = TaskLog.objects.filter(name="update_status")
    if update_status_logs.count() > 0:
        latest_update = update_status_logs.latest("finish_time").finish_time
    else:
        latest_update = None

    return render(
        request,
        "index.html",
        {
            "page_obj": page_obj,
            "proxy_list": proxy_list,
            "country_codes": country_codes,
            "location_country_code": location_country_code,
            "latest_update": latest_update if latest_update else None,
        },
    )
