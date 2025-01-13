#!/bin/bash
source /var/www/python-api/venv/bin/activate
cd /var/www/python-api
nohup gunicorn --bind 127.0.0.1:2000 app:app > /var/log/flaskapp.log 2>&1 &