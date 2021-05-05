class Centroid:
	"""Centroid"""
	def __init__(self, lat: float, lng: float):
		self._lat = lat
		self._lng = lng

	@property
	def lat(self):
		return self._lat
	
	@property
	def lng(self):
		return self._lng
