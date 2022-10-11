from rest_framework import serializers

from proxylist.models import Proxy


class ProxySerializer(serializers.ModelSerializer):
    class Meta:
        model = Proxy
        fields = [
            "id",
            "url",
            "location",
            "location_country_code",
            "location_country",
            "ip_address",
            "is_active",
            "last_checked",
            "last_active",
            "times_checked",
            "times_check_succeeded",
            "port",
        ]
        read_only_fields = [
            "id",
            "location",
            "location_country_code",
            "ip_address",
            "is_active",
            "last_checked",
            "last_active",
            "times_checked",
            "times_check_succeeded",
            "port",
        ]
