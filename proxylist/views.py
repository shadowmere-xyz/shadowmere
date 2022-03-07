import json
import re

import qrcode
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from django.views.decorators.cache import cache_page

from proxylist.base64_decoder import decode_base64
from proxylist.models import Proxy


@cache_page(60 * 20)
def list_proxies(request):
    return render(request, "index.html", {"proxy_list": Proxy.objects.filter(is_active=True).order_by('-id')})


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
    img = qrcode.make(proxy.url)
    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="qr_{proxy.id}.png"'
    img.save(response)
    return response
