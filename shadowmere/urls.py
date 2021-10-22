from django.contrib import admin
from django.urls import path

import proxylist.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', proxylist.views.list_proxies),
]
