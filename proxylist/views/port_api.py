from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets
from rest_framework.response import Response

from proxylist.models import Proxy


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
