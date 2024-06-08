from django.apps import AppConfig


class ProxylistConfig(AppConfig):
    name = "apps.proxylist"

    def ready(self) -> None:
        import apps.proxylist.signals  # noqa
