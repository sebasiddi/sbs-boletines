from .settings import *  # hereda BASE_DIR, INSTALLED_APPS, etc.
import os
from pathlib import Path

DEBUG = True

# ✅ Forzar SQLite en desarrollo
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Clave local
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
ALLOWED_HOSTS = ["*"]

print(">> Using settings_dev.py (SQLite)")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "DEBUG"},
}
