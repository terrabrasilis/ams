from ams.domain.entities import SpatialUnitInfo, DeterClassGroup


class ConfigInfo:
	"""ConfigInfo"""
	def __init__(self, spatial_units_info: 'list[SpatialUnitInfo]', 
					deter_class_groups: 'list[DeterClassGroup]',
					most_recent_risk_indicators: dict):
		self._spatial_units_info = spatial_units_info
		self._deter_class_groups = deter_class_groups
		self._most_recent_risk_indicators = most_recent_risk_indicators

	@property
	def spatial_units_info(self) -> 'list[SpatialUnitInfo]':
		return self._spatial_units_info

	@property
	def deter_class_groups(self):
		return self._deter_class_groups

	@property
	def most_recent_risk_indicators(self):
		return self._most_recent_risk_indicators
