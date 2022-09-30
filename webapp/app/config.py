import os

class Config:
	# used for frontend App
	GEOSERVER_URL = os.environ.get('GEOSERVER_URL') or 'http://localhost:8080/geoserver'
	SERVER_NAME = os.environ.get('SERVER_NAME') or '127.0.0.1:5000'
	APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT') or ''
	# used when frontend biome changes
	DB_CERRADO_URL = os.environ.get('DB_CERRADO_URL') or 'postgresql://postgres:postgres@localhost:5432/CES'
	DB_AMAZON_URL = os.environ.get('DB_AMAZON_URL') or 'postgresql://postgres:postgres@localhost:5432/AMS'
	if os.path.exists(DB_CERRADO_URL):
		DB_CERRADO_URL = open(DB_CERRADO_URL, 'r').read()
	if os.path.exists(DB_AMAZON_URL):
		DB_AMAZON_URL = open(DB_AMAZON_URL, 'r').read()

	# used for backend process
	INPUT_GEOTIFF_FUNDIARY_STRUCTURE = os.environ.get('INPUT_GEOTIFF_FUNDIARY_STRUCTURE') or 'estrutura_fundiaria_cst_2022.tif'
	BIOME = os.environ.get('BIOME') or "'Amazônia'"
	ALL_DATA = os.environ.get('ALL_DATA')=='True'

	DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://postgres:postgres@localhost:5432/AMS'
	if os.path.exists(DATABASE_URL):
		DATABASE_URL = open(DATABASE_URL, 'r').read()
	
	