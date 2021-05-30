import datetime
from .spatial_unit_feature import SpatialUnitFeature


class RiskIndicator:
	"""RiskIndicator"""
	def __init__(self, date: datetime.date, 
					percentage: float,
					area: float,
					classname: str,
					feature: SpatialUnitFeature):
		self._date = date
		self._percentage = percentage
		self._area = area
		self._classname = classname
		self._feature = feature

	@property
	def date(self) -> datetime.date:
		return self._date

	@property
	def percentage(self):
		return self._percentage

	@property
	def area(self):
		return self._area

	@property
	def classname(self):
		return self._classname

	@property
	def feature(self) -> SpatialUnitFeature:
		return self._feature
