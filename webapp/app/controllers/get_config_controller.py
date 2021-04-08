from ams.dataaccess import DataAccess
from ams.usecases import GetConfig


class GetConfigController:
	"""GetConfigController"""
	def __init__(self, da: DataAccess):
		uc = GetConfig()
		config = uc.execute(da)
		self._workspace = config.workspace
		self._spatial_units = config.spatial_units_info

	@property
	def workspace(self) -> str:
		return self._workspace
	
	@property
	def spatial_units_info(self) -> list:
		return [self._spatial_unit_info_to_dict(info) for info in self._spatial_units]

	def _spatial_unit_info_to_dict(self, suinfo):
		return {
			'dataname': suinfo.dataname,
			'center_lat': suinfo.centroid.lat,
			'center_lng': suinfo.centroid.lng
		}
	
		
