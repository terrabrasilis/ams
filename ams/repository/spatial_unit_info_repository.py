from ams import entities
from ams.dataaccess import DataAccess
from .alchemy_orm import SpatialUnitInfo
from .spatial_unit_dynamic_mapper_factory import SpatialUnitDynamicMapperFactory


class SpatialUnitInfoRepository:
	"""SpatialUnitInfoRepository"""

	def __init__(self, dataaccess: DataAccess):
		self._dataaccess = dataaccess

	def add(self, suinfo: entities.SpatialUnitInfo):
		try:
			session = self._dataaccess.create_session()
			su_orm = SpatialUnitInfo()
			su_orm.dataname = suinfo.dataname
			su_orm_class = SpatialUnitDynamicMapperFactory.instance().\
							spatial_unit_class(suinfo.dataname)
			as_attribute_name = suinfo.as_attribute_name
			if not hasattr(su_orm_class, as_attribute_name):
				raise Exception(f'Class doesn\'t have attribute \'{as_attribute_name}\'')
			su_orm.as_attribute_name = as_attribute_name
			su_orm.center_lat = suinfo.centroid.lat
			su_orm.center_lng = suinfo.centroid.lng
			session.add(su_orm)
			session.commit()
		except:
			session.rollback()
			raise
		finally:
			session.close()		

	def list(self) -> 'list[entities.SpatialUnitInfo]':
		all_data = None
		try:
			session = self._dataaccess.create_session()
			all_data = session.query(SpatialUnitInfo).all()
		except:
			session.rollback()
			raise
		finally:
			session.close()

		return [self._to_spatial_unit_info(d) for d in all_data]	

	def _to_spatial_unit_info(self, info):
		c = entities.Centroid(info.center_lat, info.center_lng)
		return entities.SpatialUnitInfo(info.dataname, info.as_attribute_name, c)
