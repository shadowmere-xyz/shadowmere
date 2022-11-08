import json
import re

import qrcode
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.defaultfilters import urlencode
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.cache import cache_page
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.response import Response

from proxylist.base64_decoder import decode_base64
from proxylist.models import Proxy
from proxylist.permissions import GeneralPermission
from proxylist.serializers import ProxySerializer


@cache_page(None)
def list_proxies(request):
    location_country_code = request.GET.get("location_country_code", "")
    country_codes = (
        Proxy.objects.filter(is_active=True)
        .order_by("location_country_code")
        .values("location_country_code")
        .distinct()
    )
    if location_country_code != "":
        proxy_list = Proxy.objects.filter(
            location_country_code=location_country_code, is_active=True
        ).order_by("-id")
    else:
        proxy_list = Proxy.objects.filter(is_active=True).order_by("-id")

    paginator = Paginator(proxy_list, 20)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "index.html",
        {
            "page_obj": page_obj,
            "proxy_list": proxy_list,
            "country_codes": country_codes,
            "location_country_code": location_country_code,
        },
    )


def healthcheck(request):
    return HttpResponse(b"OK")


def get_proxy_config(proxy):
    method_password = decode_base64(
        proxy.url.split("@")[0].replace("ss://", "").encode("ascii")
    )
    server_and_port = proxy.url.split("@")[1]
    config = {
        "server": re.findall(r"^(.*?):\d+", server_and_port)[0],
        "server_port": int(re.findall(r":(\d+)", server_and_port)[0]),
        "password": method_password.decode("ascii").split(":")[1],
        "method": method_password.decode("ascii").split(":")[0],
        "plugin": "",
        "plugin_opts": None,
        "remarks": proxy.location,
    }

    return config


def json_proxy_file(request, proxy_id):
    proxy = get_object_or_404(Proxy, id=proxy_id)
    details = get_proxy_config(proxy)
    config = {
        "server": details["server"],
        "server_port": details["server_port"],
        "local_port": 1080,
        "password": details["password"],
        "method": details["method"],
    }
    response = HttpResponse(json.dumps(config), content_type="application/json")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="shadowmere_config_{slugify(proxy.location)}.json"'
    return response


def qr_code(request, proxy_id):
    proxy = get_object_or_404(Proxy, id=proxy_id)
    img = qrcode.make(f"{proxy.url}#{urlencode(proxy.location)}")
    response = HttpResponse(content_type="image/png")
    response["Content-Disposition"] = f'attachment; filename="qr_{proxy.id}.png"'
    img.save(response)
    return response


class ProxyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows proxies to be viewed or edited.
    """

    queryset = Proxy.objects.all().order_by("-id")
    serializer_class = ProxySerializer
    permission_classes = [
        GeneralPermission,
    ]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = (
        "is_active",
        "location_country_code",
        "location_country",
        "location",
        "ip_address",
        "port",
    )

    @method_decorator(cache_page(20 * 60))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class CountryCodeViewSet(viewsets.ViewSet):
    """
    List all country codes and countries with active proxies
    """

    @method_decorator(cache_page(20 * 60))
    def list(self, request, format=None):
        country_codes = [
            {"code": code["location_country_code"], "name": code["location_country"]}
            for code in Proxy.objects.filter(is_active=True)
            .order_by("location_country_code")
            .values("location_country_code", "location_country")
            .distinct()
        ]

        return Response(country_codes)


class PortViewSet(viewsets.ViewSet):
    """
    List all available ports
    """

    @method_decorator(cache_page(20 * 60))
    def list(self, request, format=None):
        ports = [
            port
            for port in Proxy.objects.filter(is_active=True)
            .values_list("port", flat=True)
            .distinct()
            if port != 0
        ]
        ports.sort()
        ports = [
            {
                "port": port,
            }
            for port in ports
        ]
        return Response(ports)


class SubViewSet(viewsets.ViewSet):
    """
    Subscription endpoint for the shadowsocks APP
    """

    @method_decorator(cache_page(20 * 60))
    def list(self, request, format=None):
        servers = [
            get_proxy_config(server)
            for server in Proxy.objects.filter(is_active=True).order_by(
                "location_country_code"
            )
        ]
        return Response(servers)
