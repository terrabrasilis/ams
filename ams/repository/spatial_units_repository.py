from ams.domain import entities
from ams.dataaccess import DataAccess
from .alchemy_orm import SpatialUnits
from .spatial_unit_dynamic_mapper_factory import SpatialUnitDynamicMapperFactory


class SpatialUnitsRepository:
	"""SpatialUnitsRepository"""

	def __init__(self, dataaccess: DataAccess):
		self._dataaccess = dataaccess

	def add(self, su: entities.SpatialUnit, as_attribute_name: str): 
		session = self._dataaccess.create_session()
		su_orm = SpatialUnits()
		su_orm.dataname = su.name
		su_orm_class = SpatialUnitDynamicMapperFactory.instance().\
						spatial_unit_class(su.name)
		if not hasattr(su_orm_class, as_attribute_name):
			raise Exception(f'Class doesn\'t have attribute \'{as_attribute_name}\'')
		su_orm.as_attribute_name = as_attribute_name
		session.add(su_orm)
		session.commit()
		session.close()		

	def list(self):
		session = self._dataaccess.create_session()
		all_data = session.query(SpatialUnits).all()
		session.close()
		return [{'dataname': d.dataname, 'as_attribute_name': d.as_attribute_name}
				for d in all_data]	
