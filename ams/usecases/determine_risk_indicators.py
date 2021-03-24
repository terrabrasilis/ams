import datetime
from ams.domain.entities import (SpatialUnit, DeterAlerts, 
								RiskIndicator)
from ams.utils import DatetimeUtils
from ams.gis import Geoprocessing


class DetermineRiskIndicators:
	def __init__(self, su: SpatialUnit, deter_alerts: DeterAlerts, startdate: datetime.date):
		self._su = su
		self._startdate = startdate
		self._deter_alerts = deter_alerts

	def execute(self):
		enddate = DatetimeUtils.previous_month(self._startdate)
		alerts = self._deter_alerts.list(start=self._startdate, end=enddate)
		sufeats = self._su.features
		return self._calc_percentage_of_area(sufeats, alerts)

	def _calc_percentage_of_area(self, features, alerts):
		geoprocess = Geoprocessing()
		indicators = []
		for f in features:
			fgeom = f.geom
			perc = 0
			alts = []
			for a in alerts:
				if fgeom.intersects(a.geom):
					perc += geoprocess.percentage_of_area(fgeom, a.geom)
					alts.append(a)
			if perc > 0:
				indicators.append(RiskIndicator(self._startdate, perc, f, alts))
		return indicators
