from ams.geoserver import Config as GeoServerConfig
from ams.repository import SpatialUnitInfoRepository
from ams.dataaccess import DataAccess
from .config_info import ConfigInfo


class GetConfig:
	"""GetConfig"""
	def __init__(self):
		self._geoserver_config = GeoServerConfig()
		self._spatial_units_repo = None

	def execute(self, da: DataAccess) -> ConfigInfo:
		workspace = self._geoserver_config.workspace
		spatial_units_repo = SpatialUnitInfoRepository(da)
		spatial_units = spatial_units_repo.list()
		return ConfigInfo(spatial_units, workspace)
