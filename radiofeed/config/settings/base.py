from __future__ import annotations

import pathlib

from email.utils import getaddresses

import environ

from django.urls import reverse_lazy

from radiofeed import __version__

BASE_DIR = pathlib.Path(__file__).resolve(strict=True).parents[3]

env = environ.Env()

environ.Env.read_env(BASE_DIR / ".env")

DEBUG = False

SECRET_KEY = env("SECRET_KEY")

DATABASES = {
    "default": {
        **env.db(),
        "ATOMIC_REQUESTS": True,
        "CONN_MAX_AGE": 360,
    },
}

# prevent deprecation warnings
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = env("REDIS_URL")

DEFAULT_CACHE_TIMEOUT = 5 * 60

CACHES = {
    "default": {
        **env.cache("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # Mimicing memcache behavior.
            # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
            "IGNORE_EXCEPTIONS": True,
            "PARSER_CLASS": "redis.connection.HiredisParser",
        },
    },
}

EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

ADMINS = getaddresses(env.list("ADMINS", default=[]))

SITE_ID = 1

SESSION_COOKIE_DOMAIN = env("SESSION_COOKIE_DOMAIN", default=None)
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

CSRF_COOKIE_DOMAIN = env("CSRF_COOKIE_DOMAIN", default=None)
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

ROOT_URLCONF = "radiofeed.config.urls"

INSTALLED_APPS = [
    "postgres_metrics.apps.PostgresMetrics",
    "django.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.postgres",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.twitter",
    "cacheops",
    "django_extensions",
    "django_htmx",
    "django_object_actions",
    "fast_update",
    "modeltranslation",
    "widget_tweaks",
    "radiofeed.episodes",
    "radiofeed.feedparser",
    "radiofeed.podcasts",
    "radiofeed.users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "radiofeed.middleware.CacheControlMiddleware",
    "radiofeed.middleware.SearchMiddleware",
    "radiofeed.episodes.middleware.PlayerMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "radiofeed.users.middleware.LanguageMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# base Django admin URL (should be something obscure in production)

ADMIN_URL = env("ADMIN_URL", default="admin/")

# auth

AUTH_USER_MODEL = "users.User"

# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },  # noqa
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

HOME_URL = LOGIN_REDIRECT_URL = reverse_lazy("podcasts:index")

LOGIN_URL = "account_login"

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = "username_email"
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    }
}

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("fi", "Suomi"),
]
LANGUAGE_COOKIE_DOMAIN = env("LANGUAGE_COOKIE_DOMAIN", default=None)
LANGUAGE_COOKIE_SAMESITE = "Lax"

LOCALE_PATHS = [BASE_DIR / "radiofeed" / "i18n"]

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# https://docs.djangoproject.com/en/1.11/ref/forms/renderers/

FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

STATIC_URL = env("STATIC_URL", default="/static/")
STATICFILES_DIRS = [BASE_DIR / "radiofeed" / "static"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "radiofeed" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
            "builtins": [
                "radiofeed.template",
            ],
        },
    }
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
        "null": {"level": "DEBUG", "class": "logging.NullHandler"},
    },
    "loggers": {
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "django.server": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.security.DisallowedHost": {
            "handlers": ["null"],
            "propagate": False,
        },
        "django.request": {
            "level": "CRITICAL",
            "propagate": False,
        },
    },
}

# https://github.com/Suor/django-cacheops

CACHEOPS_REDIS = REDIS_URL
CACHEOPS_DEFAULTS = {"timeout": DEFAULT_CACHE_TIMEOUT}
CACHEOPS_DEGRADE_ON_FAILURE = True

CACHEOPS = {
    "podcasts.*": {"ops": "all"},
    "episodes.*": {"ops": "all"},
    "users.*": {"ops": "all"},
}

# Model translations
# https://django-modeltranslation.readthedocs.io/en/latest/installation.html#configuration

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_FALLBACK_LANGUAGES = ("en",)

# Project specific

DEFAULT_PAGE_SIZE = 30

ADMIN_SITE_HEADER = env("ADMIN_SITE_HEADER", default="Radiofeed Admin")

USER_AGENT = env(
    "USER_AGENT",
    default=f"radiofeed/{__version__} +https://github.com/danjac/radiofeed-app/",
)

CONTACT_EMAIL = env("CONTACT_EMAIL", default="admin@localhost")