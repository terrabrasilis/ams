import os


class Config:
	SERVER_URL = os.environ.get('SERVER_URL') or 'http://127.0.0.1:5000'
	DATABASE_URL = os.environ.get('DATABASE_URL') or \
			'postgresql://postgres:postgres@localhost:5432/AMS'
	DETER_DAILY_UPDATE_TIME = '01:30'
