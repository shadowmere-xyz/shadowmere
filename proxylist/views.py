import json
import re

import qrcode
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template.defaultfilters import urlencode
from django.utils.text import slugify
from django.views.decorators.cache import cache_page
from django_filters import rest_framework as filters
from rest_framework import viewsets, permissions

from proxylist.base64_decoder import decode_base64
from proxylist.models import Proxy
from proxylist.permissions import GeneralPermission
from proxylist.serializers import ProxySerializer


@cache_page(60 * 20)
def list_proxies(request):
    location_country_code = request.GET.get('location_country_code', '')
    country_codes = Proxy.objects.filter(is_active=True).order_by('location_country_code').values('location_country_code').distinct()
    if location_country_code != '':
        proxy_list = Proxy.objects.filter(
            location_country_code=location_country_code,
            is_active=True
        ).order_by('-id')
    else:
        proxy_list = Proxy.objects.filter(is_active=True).order_by('-id')

    paginator = Paginator(proxy_list, 20)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request,
                  "index.html", {
                      "page_obj": page_obj,
                      "proxy_list": proxy_list,
                      "country_codes": country_codes,
                      "location_country_code": location_country_code,
                  }
                  )


def healthcheck(request):
    return HttpResponse(b"OK")


def json_proxy_file(request, proxy_id):
    proxy = get_object_or_404(Proxy, id=proxy_id)
    method_password = decode_base64(proxy.url.split("@")[0].replace("ss://", "").encode('ascii'))
    server_and_port = proxy.url.split("@")[1]
    config = {
        "server": re.findall(r'^(.*?):\d+', server_and_port)[0],
        "server_port": int(re.findall(r":(\d+)", server_and_port)[0]),
        "local_port": 1080,
        "password": method_password.decode("ascii").split(":")[1],
        "method": method_password.decode("ascii").split(":")[0]
    }
    response = HttpResponse(json.dumps(config), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="shadowmere_config_{slugify(proxy.location)}.json"'
    return response


def qr_code(request, proxy_id):
    proxy = get_object_or_404(Proxy, id=proxy_id)
    img = qrcode.make(f'{proxy.url}#{urlencode(proxy.location)}')
    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_{proxy.id}.png"'
    img.save(response)
    return response


class ProxyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows proxies to be viewed or edited.
    """
    queryset = Proxy.objects.all().order_by('-id')
    serializer_class = ProxySerializer
    permission_classes = [GeneralPermission, ]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('is_active', 'location_country_code', 'location',)
