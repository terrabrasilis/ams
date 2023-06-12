import sys
sys.path.insert(0,'../ams')
import warnings
warnings.filterwarnings("ignore")

from webapp.app.config import Config
from ams.usecases import ActiveFires
from ams.usecases import DeterDaily
from ams.dataaccess.ftp_ibama_risk import FtpIBAMARisk
from ams.usecases import IBAMARisk
from ams.usecases.classify_by_land_use import ClassifyByLandUse

# Update all data including deter history? (see at: ~/ams/webapp/app/config.py)
alldata=Config.ALL_DATA
# For a new database or if deter_history changes at source, use True at least once.

deterupdate = DeterDaily(Config.DATABASE_URL, Config.BIOME, alldata)
deterupdate.execute()

firesupdate = ActiveFires(Config.DATABASE_URL, Config.BIOME, alldata)
firesupdate.execute()

# only for Amazonia
if Config.BIOME=='Amazônia':
    ftp = FtpIBAMARisk(Config.DATABASE_URL, host=Config.FTP_HOST, ftp_path=Config.FTP_PATH, user=Config.FTP_USER, password=Config.FTP_PASS, port=Config.FTP_PORT, output_path=Config.RISK_OUTPUT_PATH, risk_file_name=Config.RISK_INPUT_FILE)
    riskupdate = IBAMARisk(Config.DATABASE_URL, ftp=ftp)
    riskupdate.execute()

class_deter_polys = ClassifyByLandUse(Config.DATABASE_URL, Config.INPUT_GEOTIFF_FUNDIARY_STRUCTURE, alldata)
class_deter_polys.execute()