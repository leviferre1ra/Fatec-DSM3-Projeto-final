#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt

python project/manage.py collectstatic --no-input

python project/manage.py migrate