import os


class Config:
	HOMOLOGATION = os.environ.get('HOMOLOGATION') or False
	GEOSERVER_URL = os.environ.get('GEOSERVER_URL') or \
			'http://localhost:8080/geoserver'
	GEOSERVER_WORKSPACE = os.environ.get('GEOSERVER_WORKSPACE') or 'ams'
	DATABASE_URL = os.environ.get('DATABASE_URL') or \
			'postgresql://postgres:postgres@localhost:5432/AMS'
	SERVER_NAME = os.environ.get('SERVER_NAME') or '127.0.0.1:5000'
	APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT') or ''
	INPUT_GEOTIFF_FUNDIARY_STRUCTURE = os.environ.get('INPUT_GEOTIFF_FUNDIARY_STRUCTURE') or \
		'estrutura_fundiaria_cst_2022.tif'
	BIOME = os.environ.get('BIOME') or "'Amazônia'"
	ALL_DATA = os.environ.get('ALL_DATA')=='True'

	if os.path.exists(DATABASE_URL):
		DATABASE_URL = open(DATABASE_URL, 'r').read()