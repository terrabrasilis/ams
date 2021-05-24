#!/bin/bash
cd /usr/local/webapp
source .env
gunicorn --workers=4 --bind=0.0.0.0:7000 wsgi:app