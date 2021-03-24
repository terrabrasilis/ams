from .geometry import Geometry


class SpatialUnitFeature:
	"""SpatialUnitFeature"""

	def __init__(self, id: int, name: str, geom: Geometry):
		self._id = id
		self._name = name
		self._geom = geom

	@property
	def name(self) -> str:
		return self._name
	
	@property
	def geom(self) -> Geometry:
		return self._geom

	@property
	def id(self):
		return self._id
	
