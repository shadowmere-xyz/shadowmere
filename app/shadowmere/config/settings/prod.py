from .base import *  # noqa

THIRD_PARTY_APPS += "django_prometheus,"  # noqa

MIDDLEWARE.insert(  # noqa
    0,
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
)

MIDDLEWARE.append(  # noqa
    "django_prometheus.middleware.PrometheusAfterMiddleware",
)

RATELIMIT_ENABLE = True

DEFAULT_FILE_STORAGE = "minio_storage.storage.MinioMediaStorage"

STATICFILES_STORAGE = "minio_storage.storage.MinioStaticStorage"

MINIO_STORAGE_ENDPOINT = env("MINIO_ENDPOINT")  # noqa

MINIO_STORAGE_ACCESS_KEY = env("MINIO_ACCESS_KEY")  # noqa

MINIO_STORAGE_SECRET_KEY = env("MINIO_SECRET_KEY")  # noqa

MINIO_STORAGE_USE_HTTPS = True

MINIO_STORAGE_MEDIA_BUCKET_NAME = (
    f"{env('MINIO_BUCKET')}-media"  # noqa
    if env("MINIO_BUCKET") != ""  # noqa
    else "shadowmere-media"
)

MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True

MINIO_STORAGE_STATIC_BUCKET_NAME = (
    f"{env('MINIO_BUCKET')}-static"  # noqa
    if env("MINIO_BUCKET") != ""  # noqa
    else "shadowmere-static"
)

MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET = True

PROMETHEUS_METRICS_EXPORT_PORT_RANGE = range(8002, 8008)

if env("SENTRY_DSN") != "":  # noqa
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),  # noqa
        integrations=[
            DjangoIntegration(),
        ],
        traces_sample_rate=0.01,
        send_default_pii=True,
    )
