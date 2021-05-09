from .base import *  # noqa
from .base import BASE_DIR
from .mixins.aws import *  # noqa
from .mixins.aws import AWS_STATIC_CLOUDFRONT_DOMAIN, AWS_STATIC_LOCATION
from .mixins.mailgun import *  # noqa
from .mixins.secure import *  # noqa
from .mixins.sentry import *  # noqa

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# https://pypi.org/project/django-permissions-policy/

PERMISSIONS_POLICY = {
    "accelerometer": [],
    "ambient-light-sensor": [],
    "camera": [],
    "document-domain": [],
    "encrypted-media": [],
    "fullscreen": [],
    "geolocation": [],
    "gyroscope": [],
    "interest-cohort": [],
    "magnetometer": [],
    "microphone": [],
    "payment": [],
    "usb": [],
}

STATIC_URL = "https://" + AWS_STATIC_CLOUDFRONT_DOMAIN + "/" + AWS_STATIC_LOCATION + "/"
DEFAULT_FILE_STORAGE = "audiotrails.shared.storages.MediaStorage"

STATIC_ROOT = BASE_DIR / "staticfiles"

# https://github.com/jazzband/sorl-thumbnail#is-so-slow-in-amazon-s3

THUMBNAIL_FORCE_OVERWRITE = True
