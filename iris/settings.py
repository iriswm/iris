from json import loads
from os import getenv
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv

# dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
DJANGO_STATE_DIR = getenv("DJANGO_STATE_DIR", "state")
STATE_DIR = (
    (BASE_DIR / DJANGO_STATE_DIR)
    if DJANGO_STATE_DIR.startswith("/")
    else Path(DJANGO_STATE_DIR)
)

# Security
DEBUG = getenv("DJANGO_DEBUG", False)
SECRET_KEY = getenv("DJANGO_SECRET_KEY")

# Database
DJANGO_DEFAULT_DB = getenv("DJANGO_DEFAULT_DB", None)
DATABASES = {
    "default": (
        {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": "localhost",
            "PORT": 15432,
            "NAME": "iris",
            "USER": "iris",
            "PASSWORD": "iris",
        }
        if DJANGO_DEFAULT_DB is None
        else loads(DJANGO_DEFAULT_DB)
    )
}

# General framework
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "iris.app",
    "iris_wc",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "iris.app.context.stations",
                "iris.app.context.current_language",
            ],
        },
    },
]
ROOT_URLCONF = "iris.urls"
WSGI_APPLICATION = "iris.wsgi.application"
LOGIN_URL = "iris:login"

# I18N/L10N
LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", _("English")),
    ("es", _("Spanish")),
]
USE_TZ = True

# Media and static files
MEDIA_ROOT = STATE_DIR / "media"
MEDIA_URL = "media/"
STATIC_ROOT = STATE_DIR / "cdn"
STATIC_URL = "static/"
