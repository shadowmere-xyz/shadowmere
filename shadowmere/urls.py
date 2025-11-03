from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

import proxylist.views
from proxylist import views
from shadowmere import settings

router = routers.DefaultRouter()
router.register(r"proxies", views.ProxyViewSet)
router.register(r"subscriptions", views.SubscriptionViewSet)
router.register(r"country-codes", views.CountryCodeViewSet, basename="country-codes")
router.register(r"ports", views.PortViewSet, basename="ports")
router.register(r"sub", views.SubViewSet, basename="sub")
router.register(r"b64sub", views.Base64SubViewSet, basename="b64sub")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", proxylist.views.list_proxies),
    path("<int:proxy_id>/config", proxylist.views.json_proxy_file),
    path("<int:proxy_id>/qr", proxylist.views.qr_code),
    path("health", proxylist.views.healthcheck),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/", include(router.urls)),
    path("", include("django_prometheus.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
