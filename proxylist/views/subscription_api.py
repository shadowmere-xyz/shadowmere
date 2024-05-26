import base64

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_ratelimit.decorators import ratelimit
from rest_framework import viewsets
from rest_framework.response import Response

from proxylist.models import Proxy
from proxylist.proxy import get_proxy_config, get_flag_or_empty


class SubViewSet(viewsets.ViewSet):
    """
    Subscription endpoint for the shadowsocks APP
    """

    @method_decorator(
        ratelimit(
            key="ip",
            rate="3/m",
            block=True,
        )
    )
    @method_decorator(cache_page(20 * 60))
    def list(self, request, format=None):
        servers = [
            get_proxy_config(server)
            for server in Proxy.objects.filter(is_active=True).order_by(
                "location_country_code"
            )
        ]
        return Response(servers)


class Base64SubViewSet(viewsets.ViewSet):
    """
    Subscription endpoint for the v2ray and nekoray apps
    """

    @method_decorator(
        ratelimit(
            key="ip",
            rate="3/m",
            block=True,
        )
    )
    @method_decorator(cache_page(20 * 60))
    def list(self, request, format=None):
        server_list = ""
        for proxy in Proxy.objects.filter(is_active=True).order_by(
            "location_country_code"
        ):
            server_list += f"\n{proxy.url}#{get_flag_or_empty(proxy.location_country_code)} {proxy.location}"
        b64_servers = base64.b64encode(server_list.encode("utf-8"))
        return HttpResponse(b64_servers)
