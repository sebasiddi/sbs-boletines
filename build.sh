#!/usr/bin/env bash
# build.sh: Script para que Render ejecute en cada despliegue
set -eo pipefail


pip install -r requirements.txt          # Instala dependencias
python manage.py migrate                # Aplica migraciones de la BD
python manage.py collectstatic --noinput  # Recolecta archivos estáticos