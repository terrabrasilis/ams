class SpatialUnitInfo:
	"""SpatialUnitInfo"""
	def __init__(self, dataname: str, as_attribute_name: str): 
				# crs: int, center_coord: CenterCoordinate):
		self._dataname = dataname
		self._as_attribute_name = as_attribute_name
		# self._center_coord = center_coord
		# sekf._crs = crs

	# @property
	# def center(self):
	# 	return self._center_coord

	@property
	def dataname(self):
		return self._dataname
	
	@property
	def as_attribute_name(self):
		return self._as_attribute_name
		
	# @property
	# def crs(self):
	# 	return self._crs
	