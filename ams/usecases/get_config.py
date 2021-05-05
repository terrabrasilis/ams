from ams.geoserver import Config as GeoServerConfig
from ams.repository import (SpatialUnitInfoRepository,
							DeterClassGroupRepository)
from ams.dataaccess import DataAccess
from .config_info import ConfigInfo


class GetConfig:
	"""GetConfig"""
	def __init__(self):
		self._geoserver_config = GeoServerConfig()
		self._spatial_units = None
		self._deter_class_groups = None

	def execute(self, da: DataAccess) -> ConfigInfo:
		workspace = self._geoserver_config.workspace
		spatial_units_repo = SpatialUnitInfoRepository(da)
		self._spatial_units = spatial_units_repo.list()
		deter_class_group_repo = DeterClassGroupRepository(da)
		self._deter_class_groups = deter_class_group_repo.list()
		return ConfigInfo(self._spatial_units, workspace, self._deter_class_groups)
