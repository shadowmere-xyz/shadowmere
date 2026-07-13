from django.apps import AppConfig


class ProxylistConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "proxylist"

    def ready(self):
        # Register tasks in the web process so the huey stats dashboard
        # can list them; only run_huey autodiscovers the tasks module.
        from . import tasks  # noqa: F401
