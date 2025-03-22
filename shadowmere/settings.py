"""
Django settings for shadowmere project.

Generated by 'django-admin startproject' using Django 3.2.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _
from pythonjsonlogger import jsonlogger

BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", False)

SHADOWTEST_URL = os.getenv("SHADOWTEST_URL", "https://shadowtest.akiel.dev/v2/test")

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "shadowmere.xyz",
    "shadowmere.akiel.dev",
    "old.shadowmere.akiel.dev",
    "eb7x5hfb3vbb3zgrzi6qf6sqwks64fp63a7ckdl3sdw5nb6bgvskvpyd.onion",
]

CSRF_TRUSTED_ORIGINS = [
    "https://shadowmere.akiel.dev",
    "https://shadowmere.xyz",
]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "proxylist.apps.ProxylistConfig",
    "storages",
    "import_export",
    "django_prometheus",
    "rangefilter",
    "huey.contrib.djhuey",
    "rest_framework",
    "django_filters",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "shadowmere.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "shadowmere.wsgi.application"

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django_prometheus.db.backends.postgresql",
            "NAME": "shadowmere",
            "USER": "shadowmere",
            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "HOST": "db",
        }
    }

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

from pythonjsonlogger import jsonlogger

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(levelname)s %(name)s %(message)s %(asctime)s %(module)s %(task)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        # Add other loggers here as needed
    },
}


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANGUAGES = [
    ("es", _("Spanish")),
    ("en", _("English")),
]

LOCALE_PATHS = ("./locale",)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = "./static_files/"

if not DEBUG:
    STORAGES = {"staticfiles": {"BACKEND": "minio_storage.storage.MinioStaticStorage"}}
    MINIO_STORAGE_ENDPOINT = os.getenv("MINIO_ENDPOINT")
    MINIO_STORAGE_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
    MINIO_STORAGE_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
    MINIO_STORAGE_USE_HTTPS = True
    MINIO_STORAGE_MEDIA_BUCKET_NAME = (
        f"{os.getenv('MINIO_BUCKET')}-media"
        if os.getenv("MINIO_BUCKET") != ""
        else "shadowmere-media"
    )
    MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET = True
    MINIO_STORAGE_STATIC_BUCKET_NAME = (
        f"{os.getenv('MINIO_BUCKET')}-static"
        if os.getenv("MINIO_BUCKET") != ""
        else "shadowmere-static"
    )
    MINIO_STORAGE_AUTO_CREATE_STATIC_BUCKET = True

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

HUEY = {
    "huey_class": "huey.RedisHuey",  # Huey implementation to use.
    "name": "shadowmere",  # Use db name for huey.
    "results": True,  # Store return values of tasks.
    "store_none": False,  # If a task returns None, do not save to results.
    "immediate": False,  # If DEBUG=True, run synchronously.
    "utc": True,  # Use UTC for all times internally.
    "blocking": True,  # Perform blocking pop rather than poll Redis.
    "connection": {
        "host": "localhost" if DEBUG else "redis",
        "port": 6379,
        "db": 0,
        "connection_pool": None,  # Definitely you should use pooling!
        # ... tons of other options, see redis-py for details.
        # huey-specific connection parameters.
        "read_timeout": 1,  # If not polling (blocking pop), use timeout.
        "url": None,  # Allow Redis config via a DSN.
    },
    "consumer": {
        "workers": 4,
        "worker_type": "process",
        "initial_delay": 0.1,  # Smallest polling interval, same as -d.
        "backoff": 1.15,  # Exponential backoff using this rate, -b.
        "max_delay": 10.0,  # Max possible polling interval, -m.
        "scheduler_interval": 1,  # Check schedule every second, -s.
        "periodic": True,  # Enable crontab feature.
        "check_worker_health": True,  # Enable worker health checks.
        "health_check_interval": 1,  # Check worker health every second.
    },
}

AdminSite.site_header = "Shadowmere administration"

PROMETHEUS_METRICS_EXPORT_PORT_RANGE = range(8002, 8008)

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "proxylist.pagination.ProxiesPagination",
    "PAGE_SIZE": 10,
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

CONN_MAX_AGE = 60
CONN_HEALTH_CHECKS = True

if not DEBUG and os.getenv("SENTRY_DSN") != "":
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
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

RATELIMIT_ENABLE = False
RATELIMIT_VIEW = "proxylist.views.ratelimited_error"

CACHE_LOCATION_SECONDS = 300
