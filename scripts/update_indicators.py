from ams.usecases import DeterDailyUpdate, Initializer
from ams.repository import (DeterRepository,
							SpatialUnitInfoRepository)
from ams.dataaccess import AlchemyDataAccess


db_url = 'postgresql://postgres:postgres@localhost:5432/AMS'
da = AlchemyDataAccess()
da.connect(db_url)
su_info_repo = SpatialUnitInfoRepository(da)
init = Initializer(su_info_repo)
init.execute(da)
deter_repo = DeterRepository()
update = DeterDailyUpdate(deter_repo, -1, db_url)
update.execute(da, True)
