import socket

from audiotrails.config.settings.base import *  # noqa
from audiotrails.config.settings.base import INSTALLED_APPS, MIDDLEWARE, TEMPLATES

DEBUG = True
THUMBNAIL_DEBUG = True
TEMPLATES[0]["OPTIONS"]["debug"] = True

INSTALLED_APPS = ["whitenoise.runserver_nostatic"] + INSTALLED_APPS + ["silk"]

MIDDLEWARE = ["silk.middleware.SilkyMiddleware"] + MIDDLEWARE

# podman internal ips
INTERNAL_IPS = socket.gethostbyname_ex(socket.gethostname())[2]
