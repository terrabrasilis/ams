import sys
sys.path.insert(0,'../ams')
import warnings
warnings.filterwarnings("ignore")

from webapp.app.config import Config
from ams.usecases import ActiveFires
from ams.usecases import DeterDaily
from ams.usecases.classify_by_land_use import ClassifyByLandUse

# Update all data including deter history? (see at: ~/ams/webapp/app/config.py)
alldata=Config.ALL_DATA
# For a new database or if deter_history changes at source, use True at least once.

deterupdate = DeterDaily(Config.DATABASE_URL, Config.BIOME, alldata)
deterupdate.execute()

firesupdate = ActiveFires(Config.DATABASE_URL, Config.BIOME, alldata)
firesupdate.execute()

class_deter_polys = ClassifyByLandUse(Config.DATABASE_URL, Config.INPUT_GEOTIFF_FUNDIARY_STRUCTURE, alldata)
class_deter_polys.execute()