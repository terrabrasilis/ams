from ams.repository import (SpatialUnitDynamicMapperFactory,
							SpatialUnitInfoRepository)
from ams.dataaccess import DataAccess


class Initializer:
	"""Initializer"""
	def __init__(self, 
				su_info_repo: SpatialUnitInfoRepository,
				su_factory: SpatialUnitDynamicMapperFactory = SpatialUnitDynamicMapperFactory()):
		self._su_factory = su_factory
		self._su_info_repo = su_info_repo

	def execute(self, dataaccess: DataAccess):
		self._su_factory.instance().dataaccess = dataaccess
		sus_info = self._su_info_repo.list()
		for sui in sus_info:
			self._su_factory.instance().add_class_mapper(sui.dataname)		
