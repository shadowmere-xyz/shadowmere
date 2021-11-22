from django.contrib import admin
from django.contrib.auth.models import Group
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import DateRangeFilter

from proxylist.models import Proxy
from proxylist.proxy import update_proxy_status


class ProxyResource(resources.ModelResource):
    class Meta:
        model = Proxy


class ProxyAdmin(ImportExportModelAdmin):
    def update_status(modeladmin, request, queryset):
        for proxy in queryset:
            update_proxy_status(proxy)

    list_display = ('url', 'location', 'is_active', 'last_checked', 'last_active')
    fields = ['url']
    actions = [update_status, ]
    list_filter = ('is_active', ('last_active', DateRangeFilter),)
    resource_class = ProxyResource


admin.site.unregister(Group)
admin.site.register(Proxy, ProxyAdmin)
