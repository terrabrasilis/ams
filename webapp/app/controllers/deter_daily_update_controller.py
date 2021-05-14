from ams.usecases import DeterDailyUpdate
from ams.repository import DeterRepository
from ams.dataaccess import DataAccess


class DeterDailyUpdateController:
	"""DeterDailyUpdateController"""
	def __init__(self, da: DataAccess, at: str):
		deter_repo = DeterRepository()
		uc = DeterDailyUpdate(deter_repo, at)
		uc.execute(da)
