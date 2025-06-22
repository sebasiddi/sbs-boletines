from .settings import *  # Importa todo lo original

import os

DEBUG = True

# Sobrescribe la base de datos para desarrollo local con SQLite
DATABASES = {
    'default': dj_database_url.config(default=os.environ['DATABASE_URL'])
}

# Activá la key local (usás la misma que en producción si querés, o una más segura si subís a Git)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

ALLOWED_HOSTS = ["*"]

# Opcional: usar esto si querés ver errores de consola en desarrollo
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
