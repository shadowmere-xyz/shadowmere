from django.contrib import admin
from django.urls import path

import proxylist.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', proxylist.views.list_proxies),
    path('<int:proxy_id>/config', proxylist.views.json_proxy_file),
]
