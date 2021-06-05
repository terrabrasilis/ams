import os


class Config:
	GEOSERVER_URL = os.environ.get('GEOSERVER_URL') or \
			'http://localhost:8080/geoserver'
	GEOSERVER_WORKSPACE = os.environ.get('GEOSERVER_WORKSPACE') or 'ams'
	DATABASE_URL = os.environ.get('DATABASE_URL') or \
			'postgresql://postgres:postgres@localhost:5432/AMS'
	SERVER_NAME = os.environ.get('SERVER_NAME') or '127.0.0.1:5000'
	APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT') or ''
	DETER_DAILY_UPDATE_TIME_INTERVAL = os.environ.get('DETER_DAILY_UPDATE_TIME_INTERVAL') or 60
