# boletines_web/settings_transfer.py
from .settings import *
import os

# DB SQLite local de origen (ruta absoluta a tu archivo .sqlite3)
SQLITE_OLD_PATH = os.environ.get("SQLITE_OLD_PATH", os.path.join(BASE_DIR, "db.sqlite3"))

DATABASES["sqlite_old"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": SQLITE_OLD_PATH,
}

# La 'default' sigue siendo la de settings.py (Postgres vía DATABASE_URL)
