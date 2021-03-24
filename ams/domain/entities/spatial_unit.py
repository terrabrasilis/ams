from .spatial_unit_feature import SpatialUnitFeature


class SpatialUnit:
	"""SpatialUnit"""

	def __init__(self, name: str):
		self._name = name
		self._features = []
		
	def add(self, feature: SpatialUnitFeature):
		self._features.append(feature)

	@property
	def features(self) -> 'list[SpatialUnitFeature]':
		return self._features.copy()
	
