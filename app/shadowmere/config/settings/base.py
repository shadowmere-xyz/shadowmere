from pathlib import Path

import environ
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

env = environ.Env(
    SECRET_KEY=(str, ""),
    DEBUG=(bool, False),
    SHADOWTEST_URL=(str, ""),
    ALLOWED_HOSTS=(str, ""),
    CSRF_TRUSTED_ORIGINS=(str, ""),
    MINIO_ENDPOINT=(str, ""),
    MINIO_ACCESS_KEY=(str, ""),
    MINIO_SECRET_KEY=(str, ""),
    MINIO_BUCKET=(str, ""),
    SENTRY_DSN=(str, ""),
    REDIS_HOST=(str, ""),
    REDIS_PORT=(int, 0),
)

SECRET_KEY = env("SECRET_KEY")

DEBUG = env("DEBUG", default=False)

SHADOWTEST_URL = env("SHADOWTEST_URL")

ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(" ")

CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS").split(" ")

SITE_ID = 1

APPS_DIR = BASE_DIR / "apps"

DJANGO_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "storages",
    "import_export",
    "rangefilter",
    "huey.contrib.djhuey",
    "rest_framework",
    "django_filters",
]

LOCAL_APPS = ["apps.proxylist"]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_ratelimit.middleware.RatelimitMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": env.db()}

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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[%(server_time)s] %(message)s",
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        },
        # Custom handler which we will use with logger 'django'.
        # We want errors/warnings to be logged when DEBUG=False
        "console_on_not_debug": {
            "level": "WARNING",
            "filters": ["require_debug_false"],
            "class": "logging.StreamHandler",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "console_on_not_debug"],
            "level": "INFO",
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

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

STATIC_URL = "/static/"

STATIC_ROOT = "./static_files/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

HUEY = {
    "huey_class": "huey.RedisHuey",
    "name": "shadowmere",
    "results": True,
    "store_none": False,
    "immediate": False,
    "utc": True,
    "blocking": True,
    "connection": {
        "host": env("REDIS_HOST", default="redis"),
        "port": env("REDIS_PORT", default=6379),
        "db": 0,
        "connection_pool": None,
        "read_timeout": 1,
        "url": None,
    },
    "consumer": {
        "workers": 4,
        "worker_type": "process",
        "initial_delay": 0.1,
        "backoff": 1.15,
        "max_delay": 10.0,
        "scheduler_interval": 1,
        "periodic": True,
        "check_worker_health": True,
        "health_check_interval": 1,
    },
}

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "apps.proxylist.pagination.ProxiesPagination",
    "PAGE_SIZE": 10,
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

RATELIMIT_VIEW = "apps.proxylist.views.ratelimited_error"

JAZZMIN_SETTINGS = {
    "site_title": "Shadowmere Admin",
    "site_header": "Shadowmere",
    "site_brand": "Shadowmere",
    "welcome_sign": "Welcome to Shadowmere Admin",
}
