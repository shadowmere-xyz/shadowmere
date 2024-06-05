from apps.proxylist.views import (
    Base64SubViewSet,
    CountryCodeViewSet,
    PortViewSet,
    ProxyViewSet,
    SubViewSet,
    healthcheck,
    json_proxy_file,
    list_proxies,
    qr_code,
)
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"proxies", ProxyViewSet)
router.register(r"country-codes", CountryCodeViewSet, basename="country-codes")
router.register(r"ports", PortViewSet, basename="ports")
router.register(r"sub", SubViewSet, basename="sub")
router.register(r"b64sub", Base64SubViewSet, basename="b64sub")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", list_proxies),
    path("<int:proxy_id>/config", json_proxy_file),
    path("<int:proxy_id>/qr", qr_code),
    path("health", healthcheck),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/", include(router.urls)),
    path("", include("django_prometheus.urls")),
]
