from .centroid import Centroid


class SpatialUnitInfo:
	"""SpatialUnitInfo"""
	def __init__(self, dataname: str, as_attribute_name: str, centroid: Centroid): 
		self._dataname = dataname
		self._as_attribute_name = as_attribute_name
		self._centroid = centroid

	@property
	def dataname(self):
		return self._dataname
	
	@property
	def as_attribute_name(self):
		return self._as_attribute_name
		
	@property
	def centroid(self):
		return self._centroid
	