from ams.domain.entities import SpatialUnitInfo, DeterClassGroup


class ConfigInfo:
	"""ConfigInfo"""
	def __init__(self, spatial_units_info: 'list[SpatialUnitInfo]', 
					workspace: str,
					deter_class_groups: 'list[DeterClassGroup]'):
		self._spatial_units_info = spatial_units_info
		self._workspace = workspace
		self._deter_class_groups = deter_class_groups

	@property
	def spatial_units_info(self) -> 'list[SpatialUnitInfo]':
		return self._spatial_units_info

	@property
	def workspace(self) -> str:
		return self._workspace

	@property
	def deter_class_groups(self):
		return self._deter_class_groups
