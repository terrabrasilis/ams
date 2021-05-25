import time
import threading
from datetime import datetime
from ams.repository import (DeterRepository,
							SpatialUnitInfoRepository,
							DeterClassGroupRepository,
							RiskIndicatorsRepository,
							SpatialUnitDynamicMapperFactory)
from ams.dataaccess import DataAccess
from ams.usecases import DetermineRiskIndicators


class DeterDailyUpdate:
	"""DeterDailyUpdate"""
	def __init__(self, deter_repo: DeterRepository, at: str):
		self._deter_repo = deter_repo
		self._at = at
		self._sleep_sec = 10
		self._deter_last_row = None
		self._terminate = False
		self._thread_finished = False

	def execute(self, dataaccess: DataAccess):
		self._deter_last_row = self._deter_repo.list(limit=1)[0]
		self._dataaccess = dataaccess
		self._thread = threading.Thread(target=self._schedule)
		self._thread.daemon = True
		self._thread.start()

	def _schedule(self):
		while not self._terminate:
			time.sleep(self._sleep_sec)	
			if datetime.now().strftime('%H:%M') == self._at:
				self._check()
				while ((datetime.now().strftime('%H:%M') == self._at) 
						and (not self._terminate)):
					time.sleep(self._sleep_sec)

	def terminate(self):
		self._terminate = True
		self._thread.join(1)
		self._thread_finished = True

	def last_update(self):
		return self._deter_last_row.date.isoformat()

	def _check(self):
		last_row = self._deter_repo.list(limit=1)[0]
		if last_row.id != self._deter_last_row.id:
			self._determine_risks(last_row.date)
			self._deter_last_row = last_row

	def _determine_risks(self, startdate):
		sus_repo = SpatialUnitInfoRepository(self._dataaccess)
		sus_info = sus_repo.list()
		enddate = self._get_enddate()	
		groups_repo = DeterClassGroupRepository(self._dataaccess)
		class_groups = groups_repo.list()
		for su_info in sus_info:
			sutablename = su_info.dataname
			as_attribute_name = su_info.as_attribute_name
			surepo = SpatialUnitDynamicMapperFactory.instance()\
						.create_spatial_unit(sutablename, as_attribute_name)
			su = surepo.get()
			rirepo = RiskIndicatorsRepository(sutablename, as_attribute_name, self._dataaccess)
			uc = DetermineRiskIndicators(su, self._deter_repo, [], class_groups, startdate, enddate)	
			indicators = uc.execute()
			rirepo.overwrite_from_date(indicators, enddate)		

	# rebuild all deter_table data
	# because old data can change from Deter team
	def _get_enddate(self):
		oldest_data = self._deter_repo.list()[-1]
		return oldest_data.date  
