import datetime
from ams.domain.entities import (SpatialUnit, DeterAlerts, 
								RiskIndicator)
from ams.gis import Geoprocessing


class DetermineRiskIndicators:
	def __init__(self, su: SpatialUnit, deter_alerts: DeterAlerts, 
				startdate: datetime.date, enddate: datetime.date = None):
		self._su = su
		self._startdate = startdate
		self._enddate = enddate if enddate else startdate
		self._deter_alerts = deter_alerts

	def execute(self):
		alerts = self._deter_alerts.list(start=self._startdate, end=self._enddate)
		sufeats = self._su.features
		return self._calc_percentage_of_area(sufeats, alerts)

	def _calc_percentage_of_area(self, features, alerts):
		geoprocess = Geoprocessing()
		indicators = []		
		for f in features:
			fgeom = f.geom
			perc = 0
			alts = []
			currdate = alerts[0].date
			i = 0
			while i < len(alerts):
				a = alerts[i]
				if a.date == currdate:
					if fgeom.intersects(a.geom):
						perc += geoprocess.percentage_of_area(fgeom, a.geom)
						alts.append(a)
					i += 1
				else:
					if perc > 0:
						indicators.append(RiskIndicator(currdate, perc, f, alts))
					currdate = a.date	
					perc = 0
					alts = []
			if perc > 0:
				indicators.append(RiskIndicator(currdate, perc, f, alts))
		return indicators
