from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client.registry import Collector

from proxylist.models import Proxy


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


def register_metrics() -> None:
    REGISTRY.register(CustomCollector())
