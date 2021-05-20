import os


class Config:
	GEOSERVER_URL = os.environ.get('SERVER_URL') or \
			'http://localhost:8080/geoserver'
	GEOSERVER_WORKSPACE = os.environ.get('GEOSERVER_WORKSPACE') or 'ams'
	DATABASE_URL = os.environ.get('DATABASE_URL') or \
			'postgresql://postgres:postgres@localhost:5432/AMS'
	DETER_DAILY_UPDATE_TIME = '01:30'
