import datetime
from .spatial_unit_feature import SpatialUnitFeature
from .deter_alert import DeterAlert


class RiskIndicator:
	"""RiskIndicator"""
	def __init__(self, date: datetime.date, 
					percentage: float,
					feature: SpatialUnitFeature, 
					alerts: 'list[DeterAlert]'):
		self._date = date
		self._percentage = percentage
		self._feature = feature
		self._alerts = alerts

	@property
	def date(self) -> datetime.date:
		return self._date

	@property
	def percentage(self):
		return self._percentage
	
	@property
	def feature(self) -> SpatialUnitFeature:
		return self._feature
	
	@property
	def alerts(self) -> 'list[DeterAlert]':
		return self._alerts
