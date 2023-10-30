import os

class Config:
	# used for frontend App
	GEOSERVER_URL = os.environ.get('GEOSERVER_URL') or 'http://terrabrasilis.dpi.inpe.br/geoserver'
	SERVER_NAME = os.environ.get('SERVER_NAME') or '127.0.0.1:5000'
	APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT') or ''
	# used when frontend biome changes
	DB_CERRADO_URL = os.environ.get('DB_CERRADO_URL') or 'postgresql://postgres:postgres@150.163.17.75:5444/CES'
	DB_AMAZON_URL = os.environ.get('DB_AMAZON_URL') or 'postgresql://postgres:postgres@150.163.17.75:5444/AMS4H'
	if os.path.exists(DB_CERRADO_URL):
		DB_CERRADO_URL = open(DB_CERRADO_URL, 'r').read()
	if os.path.exists(DB_AMAZON_URL):
		DB_AMAZON_URL = open(DB_AMAZON_URL, 'r').read()
