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

deterupdate = DeterDaily(db_url=Config.DATABASE_URL, biome=Config.BIOME, alldata=alldata)
deterupdate.execute()

firesupdate = ActiveFires(db_url=Config.DATABASE_URL, biome=Config.BIOME, alldata=alldata)
firesupdate.execute()

# only for Amazonia
if Config.BIOME=="Amazônia":
    ftp = FtpIBAMARisk(db_url=Config.DATABASE_URL, ftp_host=Config.FTP_HOST, ftp_path=Config.FTP_PATH,
                       ftp_user=Config.FTP_USER, ftp_password=Config.FTP_PASS, ftp_port=Config.FTP_PORT,
                       output_path=Config.RISK_OUTPUT_PATH)
    riskupdate = IBAMARisk(db_url=Config.DATABASE_URL, ftp=ftp)
    riskupdate.execute()

# land Use classifier
luc = ClassifyByLandUse(biome=Config.BIOME, db_url=Config.DATABASE_URL, input_tif=Config.INPUT_GEOTIFF_FUNDIARY_STRUCTURE, alldata=alldata)
luc.execute()