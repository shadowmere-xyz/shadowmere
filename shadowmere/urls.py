from django.contrib import admin
from django.urls import path, include

import proxylist.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', proxylist.views.list_proxies),
    path('<int:proxy_id>/config', proxylist.views.json_proxy_file),
    path('<int:proxy_id>/qr', proxylist.views.qr_code),
    path('health', proxylist.views.healthcheck),
    path('', include('django_prometheus.urls')),
]
