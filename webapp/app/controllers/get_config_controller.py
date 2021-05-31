from ams.dataaccess import DataAccess
from ams.usecases import GetConfig


class GetConfigController:
	"""GetConfigController"""
	def __init__(self, da: DataAccess):
		uc = GetConfig()
		config = uc.execute(da)
		self._spatial_units = config.spatial_units_info
		self._deter_class_groups = config.deter_class_groups
		self._most_recent_risk_indicators = config.most_recent_risk_indicators
	
	@property
	def spatial_units_info(self) -> list:
		return [self._spatial_unit_info_to_dict(info) for info in self._spatial_units]

	def _spatial_unit_info_to_dict(self, suinfo):
		return {
			'dataname': suinfo.dataname,
			'center_lat': suinfo.centroid.lat,
			'center_lng': suinfo.centroid.lng,
			'last_date': self._most_recent_risk_indicators[suinfo.dataname].date.isoformat()
		}

	@property
	def deter_class_groups(self) -> list:
		return [self._deter_class_groups_to_dict(group) for group in self._deter_class_groups]

	def _deter_class_groups_to_dict(self, group):
		return {
			'name': group.name,
			'classes': [clas for clas in group.classes],
		}		
