from django.shortcuts import render

from proxylist.models import Proxy


def list_proxies(request):
    return render(request, "index.html", {"proxy_list": Proxy.objects.filter(is_active=True)})
