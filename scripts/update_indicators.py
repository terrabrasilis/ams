import sys
sys.path.insert(0,'..')
import warnings
warnings.filterwarnings("ignore")
from ams.usecases import DeterDailyUpdate
from ams.usecases import Initializer
from ams.repository import (DeterRepository,
							SpatialUnitInfoRepository)
from ams.dataaccess import AlchemyDataAccess
from webapp.app.config import Config
from ams.usecases.classify_deter_polygons import ClassifyDeterPolygons

da = AlchemyDataAccess()
da.connect(Config.DATABASE_URL)
su_info_repo = SpatialUnitInfoRepository(da)
init = Initializer(su_info_repo)
init.execute(da)
deter_repo = DeterRepository()
update = DeterDailyUpdate(deter_repo, -1, Config.DATABASE_URL)
update.execute(da, True)

class_deter_polys = ClassifyDeterPolygons(Config.DATABASE_URL)
class_deter_polys.execute()
