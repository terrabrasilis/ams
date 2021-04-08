from ams.domain.entities import SpatialUnitInfo


class ConfigInfo:
	"""ConfigInfo"""
	def __init__(self, spatial_units_info: 'list[SpatialUnitInfo]', workspace: str):
		self._spatial_units_info = spatial_units_info
		self._workspace = workspace
		
	@property
	def spatial_units_info(self) -> 'list[SpatialUnitInfo]':
		return self._spatial_units_info

	@property
	def workspace(self) -> str:
		return self._workspace
