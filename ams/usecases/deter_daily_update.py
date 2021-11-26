from os import path
import time
import threading
import traceback
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from ams.repository import (DeterRepository,
							SpatialUnitInfoRepository,
							DeterClassGroupRepository,
							RiskIndicatorsRepository,
							SpatialUnitDynamicMapperFactory)
from ams.dataaccess import DataAccess
from ams.usecases import DetermineRiskIndicators


class DeterDailyUpdate:
	"""DeterDailyUpdate"""
	def __init__(self, deter_repo: DeterRepository, every_in_minutes: int, db_url: str = ''):
		self._scriptspath = path.join(path.dirname(__file__), '../../scripts')
		self._db_url = db_url
		#self._enabled = every_in_minutes > -1
		self._enabled = False
		self._now = False
		self._deter_repo = deter_repo
		self._every = every_in_minutes
		self._update_time = self._get_next_update_time()
		self._sleep_sec = 10
		self._deter_last_row = None
		self._terminate = False
		self._thread_finished = False

	def _update_from_deter_r(self):
		with open(f'{self._scriptspath}/script_fill_deter_public_deter_all.sql', encoding='UTF-8') as scriptfile:
			script = scriptfile.read()
		with create_engine(self._db_url).connect() as con:
			con.connect()
			con.execute(script)

	def _get_next_update_time(self):
		return (datetime.now() + timedelta(minutes=self._every)).strftime('%H:%M')

	def _do_updates(self):
		try:
			self._check()
			self._update_from_deter_r()
		except Exception:
			print(traceback.format_exc())

	def execute(self, dataaccess: DataAccess, now: bool = False):
		self._now = now
		self._deter_last_row = self._deter_repo.list(limit=1)[0]
		self._dataaccess = dataaccess
		self._check()
		if self._now:
			self._do_updates()
		elif self._enabled:
			self._thread = threading.Thread(target=self._schedule)
			self._thread.daemon = True
			self._thread.start()

	def _schedule(self):
		while not self._terminate:
			time.sleep(self._sleep_sec)
			if datetime.now().strftime('%H:%M') < self._update_time:
				continue
			at = datetime.now().strftime('%Y-%m-%d %H:%M:%S %p')
			print(f'AMS daily update was fired at {at}.')  # TODO(#59)
			self._do_updates()
			self._update_time = self._get_next_update_time()

	def terminate(self):
		self._terminate = True
		if self._thread:
			self._thread.join(1)
			self._thread_finished = True

	def last_update(self):
		return self._deter_last_row.date.isoformat()

	def _check(self):
		last_row = self._deter_repo.list(limit=1)[0]
		if (last_row.id != self._deter_last_row.id
				or self._has_indicator_dalayed()):
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

	def _has_indicator_dalayed(self):
		sus_repo = SpatialUnitInfoRepository(self._dataaccess)
		sus_info = sus_repo.list()
		for su_info in sus_info:
			sutablename = su_info.dataname
			as_attribute_name = su_info.as_attribute_name
			rirepo = RiskIndicatorsRepository(sutablename, as_attribute_name, self._dataaccess)
			ri_most_recent = rirepo.get_most_recent()
			if self._deter_last_row.date > ri_most_recent.date:
				return True
		return False
