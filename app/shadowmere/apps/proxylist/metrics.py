from apps.proxylist.models import Proxy
from prometheus_client.core import REGISTRY, GaugeMetricFamily
from prometheus_client.registry import Collector


class CustomCollector(Collector):
    def collect(self):
        yield GaugeMetricFamily(
            "shadowmere_proxies_total",
            "The total number of registered proxies",
            value=Proxy.objects.count(),
        )
        yield GaugeMetricFamily(
            "shadowmere_active_proxies_total",
            "The total number of active proxies",
            value=Proxy.objects.filter(is_active=True).count(),
        )


def register_metrics():
    REGISTRY.register(CustomCollector())
