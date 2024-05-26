from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets
from rest_framework.response import Response

from proxylist.models import Proxy


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
