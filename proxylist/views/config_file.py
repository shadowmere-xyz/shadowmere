import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django_ratelimit.decorators import ratelimit

from proxylist.models import Proxy
from proxylist.proxy import get_proxy_config


@ratelimit(
    key="ip",
    rate="1/s",
    block=True,
)
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
    response["Content-Disposition"] = (
        f'attachment; filename="shadowmere_config_{slugify(proxy.location)}.json"'
    )
    return response
