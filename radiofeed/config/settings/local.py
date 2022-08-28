from __future__ import annotations

from debug_toolbar.settings import PANELS_DEFAULTS
from split_settings.tools import include

from radiofeed.config.settings.base import ADMIN_SITE_HEADER, INSTALLED_APPS, MIDDLEWARE

include("base.py")

DEBUG = True

ADMIN_SITE_HEADER += " [LOCAL]"

INSTALLED_APPS = [
    "whitenoise.runserver_nostatic",
    "debug_toolbar",
    "silk",
] + INSTALLED_APPS

MIDDLEWARE += [
    "silk.middleware.SilkyMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

INTERNAL_IPS = ["127.0.0.1"]

DEBUG_ERROR_PAGES = True

DEBUG_TOOLBAR_PANELS = PANELS_DEFAULTS + ["cachalot.panels.CachalotPanel"]
