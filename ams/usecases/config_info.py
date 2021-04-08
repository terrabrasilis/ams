from ams.domain.entities import SpatialUnitInfo


class ConfigInfo:
	"""ConfigInfo"""
	def __init__(self, spatial_units: 'list[SpatialUnitInfo]', workspace: str):
		self.spatial_units = spatial_units
		self.workspace = workspace
		
	def spatial_units_str(self):
		return [{'dataname': info.dataname} for info in self.spatial_units]
