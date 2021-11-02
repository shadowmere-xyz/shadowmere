import base64
import json
import re

import qrcode
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify

from proxylist.models import Proxy


def list_proxies(request):
    return render(request, "index.html", {"proxy_list": Proxy.objects.filter(is_active=True).order_by("location")})


def json_proxy_file(request, proxy_id):
    proxy = get_object_or_404(Proxy, id=proxy_id)
    method_password = decode_base64(proxy.url.split("@")[0].replace("ss://", "").encode('ascii'))
    server_and_port = proxy.url.split("@")[1]
    config = {
        "server": re.findall(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', server_and_port)[0],
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


def decode_base64(data, altchars=b'+/'):
    """Decode base64, padding being optional.
    source: https://stackoverflow.com/questions/2941995/python-ignore-incorrect-padding-error-when-base64-decoding
    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    data = re.sub(rb'[^a-zA-Z0-9%s]+' % altchars, b'', data)  # normalize
    missing_padding = len(data) % 4
    if missing_padding:
        data += b'=' * (4 - missing_padding)
    return base64.b64decode(data, altchars)
