#!/usr/bin/env bash
# Build script para Render

set -o errexit  # Salir si algún comando falla

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
