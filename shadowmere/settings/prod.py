from .base import *  # noqa
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

MIDDLEWARE = (
    ["django_prometheus.middleware.PrometheusBeforeMiddleware"]
    + MIDDLEWARE
    + ["django_prometheus.middleware.PrometheusAfterMiddleware"]
)

THIRD_PARTY_APPS += ["django_prometheus"]

DEFAULT_FILE_STORAGE = "minio_storage.storage.MinioMediaStorage"

STATICFILES_STORAGE = "minio_storage.storage.MinioStaticStorage"

MINIO_STORAGE_ENDPOINT = env("MINIO_ENDPOINT")

MINIO_STORAGE_ACCESS_KEY = env("MINIO_ACCESS_KEY")

MINIO_STORAGE_SECRET_KEY = env("MINIO_SECRET_KEY")

MINIO_STORAGE_USE_HTTPS = True

MINIO_STORAGE_MEDIA_BUCKET_NAME = "shadowmere-media"

MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True

MINIO_STORAGE_STATIC_BUCKET_NAME = "shadowmere-static"

MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET = True

sentry_sdk.init(
    dsn=env("SENTRY_DSN"),
    integrations=[
        DjangoIntegration(),
    ],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=0.01,
    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,
)

PROMETHEUS_METRICS_EXPORT_PORT_RANGE = range(8002, 8008)
