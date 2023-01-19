#!/bin/sh
cd /usr/local/webapp
source .env
# using the gunicorn as a WSGI server
gunicorn --workers=4 --bind=0.0.0.0:7000 'wsgi:create_app()'
