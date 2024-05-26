import qrcode
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import urlencode
from django_ratelimit.decorators import ratelimit

from proxylist.models import Proxy


@ratelimit(
    key="ip",
    rate="1/s",
    block=True,
)
def qr_code(request, proxy_id):
    proxy = get_object_or_404(Proxy, id=proxy_id)
    img = qrcode.make(f"{proxy.url}#{urlencode(proxy.location)}")
    response = HttpResponse(content_type="image/png")
    response["Content-Disposition"] = f'attachment; filename="qr_{proxy.id}.png"'
    img.save(response)
    return response
