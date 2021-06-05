from ams.usecases import DeterDailyUpdate, Initializer
from ams.repository import DeterRepository, SpatialUnitInfoRepository
from ams.dataaccess import DataAccess


class InitializerController:
	"""InitializerController"""
	def __init__(self, da: DataAccess, every_in_minutes: int):
		deter_repo = DeterRepository()
		su_info_repo = SpatialUnitInfoRepository(da)
		init = Initializer(su_info_repo)
		init.execute(da)
		deter_daily_update = DeterDailyUpdate(deter_repo, every_in_minutes)
		deter_daily_update.execute(da)
