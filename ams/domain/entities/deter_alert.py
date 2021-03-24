from .geometry import Geometry


class DeterAlert:
	"""DeterAlert"""
	def __init__(self, id, classname, date, geom):
		self._id = id
		self._classname = classname
		self._date = date
		self._geom = geom

	@property
	def id(self):
		return self._id

	@property
	def classname(self):
		return self._classname
	
	@property
	def date(self):
		return self._date		
	
	@property
	def geom(self):
		return self._geom
		