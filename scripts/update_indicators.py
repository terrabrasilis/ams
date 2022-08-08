import sys
sys.path.insert(0,'../ams')
import warnings
warnings.filterwarnings("ignore")

from webapp.app.config import Config
from ams.usecases import ActiveFires
from ams.usecases import DeterDaily
from ams.usecases.classify_by_land_use import ClassifyByLandUse

# update all data including deter history. For Active Fires, use all data from raw database.
alldata=False

deterupdate = DeterDaily(Config.DATABASE_URL, alldata)
deterupdate.execute()

firesupdate = ActiveFires(Config.DATABASE_URL, alldata=True)
firesupdate.execute()

class_deter_polys = ClassifyByLandUse(Config.DATABASE_URL, Config.INPUT_GEOTIFF_FUNDIARY_STRUCTURE, alldata)
class_deter_polys.execute()