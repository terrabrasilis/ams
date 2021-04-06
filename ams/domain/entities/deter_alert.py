import datetime
from .geometry import Geometry


class DeterAlert:
	"""DeterAlert"""
	def __init__(self, id, classname, date, geom):
		self._id = id
		self._classname = classname
		self._date = date
		self._geom = geom

	@property
	def id(self) -> int:
		return self._id

	@property
	def classname(self) -> str:
		return self._classname
	
	@property
	def date(self) -> datetime.date:
		return self._date		
	
	@property
	def geom(self) -> Geometry:
		return self._geom
