from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters import rest_framework as filters
from django_ratelimit.decorators import ratelimit
from rest_framework import viewsets

from proxylist.models import Proxy
from proxylist.permissions import GeneralPermission
from proxylist.serializers import ProxySerializer


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

    @method_decorator(ratelimit(key="ip", rate="3/s", block=True, method=["GET"]))
    @method_decorator(cache_page(20 * 60))
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
