import datetime
from ams.domain.entities import (SpatialUnit, DeterAlerts, 
								RiskIndicator, DeterClassGroup)
from ams.gis import Geoprocessing


class DetermineRiskIndicators:
	def __init__(self, su: SpatialUnit, 
				deter_alerts: DeterAlerts, 
				class_groups: 'list[DeterClassGroup]',
				startdate: datetime.date, enddate: datetime.date = None):
		self._su = su
		self._startdate = startdate
		self._enddate = enddate if enddate else startdate
		self._deter_alerts = deter_alerts
		self._class_groups = class_groups
		self._class_group_mapper = self._mapper_class_groups()

	def execute(self):
		alerts = self._deter_alerts.list(start=self._startdate, end=self._enddate)
		sufeats = self._su.features
		return self._calc_percentage_of_area(sufeats, alerts)

	def _calc_percentage_of_area(self, features, alerts):
		geoprocess = Geoprocessing()
		indicators = []		
		for f in features:
			fgeom = f.geom
			percentages = self._clear_percentages()
			currdate = alerts[0].date
			i = 0
			while i < len(alerts):
				a = alerts[i]
				if a.date == currdate:
					if fgeom.intersects(a.geom):
						group = self._get_class_group(a.classname)
						percentages[group] += geoprocess.percentage_of_area(fgeom, a.geom)
					i += 1
				else:
					self._add_percentages(indicators, percentages, f, currdate)
					currdate = a.date	
					percentages = self._clear_percentages()
			self._add_percentages(indicators, percentages, f, currdate)
		return indicators

	def _mapper_class_groups(self):
		class_groups_mapper = {}
		for g in self._class_groups:
			for c in g.classes:
				class_groups_mapper[c] = g.name
		return class_groups_mapper

	def _get_class_group(self, classname):
		if classname in self._class_group_mapper:
			return self._class_group_mapper[classname]
		return ''

	def _clear_percentages(self):
		percentages = {}
		if len(self._class_group_mapper) > 0:
			for cg in self._class_groups:
				percentages[cg.name] = 0 
			return percentages
		else:
			percentages[''] = 0 
			return percentages

	def _add_percentages(self, indicators, percentages, feature, currdate):
		if len(percentages) > 0:
			for k in percentages.keys():
				if percentages[k] > 0:
					indicators.append(RiskIndicator(currdate, percentages[k], k, feature))		
