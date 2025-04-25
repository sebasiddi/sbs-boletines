#!/usr/bin/env bash
set -eo pipefail

pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput  # ¡Esta línea es crucial!