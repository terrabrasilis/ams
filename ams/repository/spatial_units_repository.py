from sqlalchemy.orm import sessionmaker, scoped_session
from ams.domain import entities
from .alchemy_orm import SpatialUnits
from .spatial_unit_dynamic_mapper_factory import SpatialUnitDynamicMapperFactory


class SpatialUnitsRepository:
	"""SpatialUnitsRepository"""

	def __init__(self, engine):
		self._engine = engine

	def add(self, su: entities.SpatialUnit, as_attribute_name: str):
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		su_orm = SpatialUnits()
		su_orm.name = su.name
		su_orm_class = SpatialUnitDynamicMapperFactory.instance().\
						spatial_unit_class(su.name)
		if not hasattr(su_orm_class, as_attribute_name):
			raise Exception(f'Class doesn\'t have attribute \'{as_attribute_name}\'')
		su_orm.as_attribute_name = as_attribute_name
		session.add(su_orm)
		session.commit()
		session.close()		

	def list(self):
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		all_data = session.query(SpatialUnits).all()
		session.close()
		return [{'name': d.name, 'as_attribute_name': d.as_attribute_name}
				for d in all_data]	
