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
	
	# used for ETL of IBAMA risk
	FTP_HOST = os.environ.get('FTP_HOST') or "ftp.com.br"
	FTP_PORT = os.environ.get('FTP_PORT') or "21"
	FTP_PATH = os.environ.get('FTP_PATH') or "/"
	FTP_USER = os.environ.get('FTP_USER') or "user"
	FTP_PASS = os.environ.get('FTP_PASS') or "secret_password"
	# local where write the file copied from ftp
	RISK_OUTPUT_PATH = os.environ.get('RISK_OUTPUT_PATH') or "/"
	RISK_INPUT_FILE = os.environ.get('RISK_INPUT_FILE') or "Risk_areas_AMZL.tif"
	
	