from django.contrib import admin
from django.contrib.auth.models import Group

from proxylist.models import Proxy
from proxylist.proxy import update_proxy_status


class ProxyAdmin(admin.ModelAdmin):
    def update_status(modeladmin, request, queryset):
        for proxy in queryset:
            update_proxy_status(proxy)

    list_display = ('url', 'location', 'is_active', 'last_checked',)
    fields = ['url']
    actions = [update_status, ]


admin.site.unregister(Group)
admin.site.register(Proxy, ProxyAdmin)
