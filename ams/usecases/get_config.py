from ams.repository import (SpatialUnitInfoRepository,
							DeterClassGroupRepository,
							RiskIndicatorsRepository,
							SpatialUnitDynamicMapperFactory)
from ams.dataaccess import DataAccess
from .config_info import ConfigInfo


class GetConfig:
	"""GetConfig"""
	def __init__(self):
		self._spatial_units = None
		self._deter_class_groups = None

	def execute(self, da: DataAccess) -> ConfigInfo:
		spatial_units_repo = SpatialUnitInfoRepository(da)
		self._spatial_units = spatial_units_repo.list()
		deter_class_group_repo = DeterClassGroupRepository(da)
		self._deter_class_groups = deter_class_group_repo.list()
		self._most_recent_risk_indicators = self._get_most_recent_risk_indicators(da)
		return ConfigInfo(self._spatial_units, 
							self._deter_class_groups, 
							self._most_recent_risk_indicators)

	def _get_most_recent_risk_indicators(self, da):
		result = {}
		SpatialUnitDynamicMapperFactory.instance().dataaccess = da
		for sui in self._spatial_units:
			dataname = sui.dataname
			SpatialUnitDynamicMapperFactory.instance().add_class_mapper(dataname)
			rirepo = RiskIndicatorsRepository(dataname, sui.as_attribute_name, da)
			result[dataname] = rirepo.get_most_recent()
		return result	
