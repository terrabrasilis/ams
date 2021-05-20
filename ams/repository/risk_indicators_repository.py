import datetime
from sqlalchemy import desc
from ams.domain.entities import RiskIndicator
from ams.dataaccess import DataAccess
from .spatial_unit_dynamic_mapper_factory import SpatialUnitDynamicMapperFactory


class RiskIndicatorsRepository:
	"""RiskIndicatorsRepository"""

	def __init__(self, spatial_unit_tablename: str, 
						spatial_unit_as_attribute_name: str,
						dataaccess: DataAccess):
		self._dataaccess = dataaccess
		self._engine = dataaccess.engine
		self._spatial_unit_tablename = spatial_unit_tablename
		self._spatial_unit_as_attribute_name = spatial_unit_as_attribute_name
		self._tablename = f'{spatial_unit_tablename}_risk_indicators'

	def list(self) -> 'list[RiskIndicator]': 
		session = self._dataaccess.create_session()
		riclass = SpatialUnitDynamicMapperFactory.instance().\
						risk_indicator_class(self._spatial_unit_tablename)
		all_data = session.query(riclass).all()
		session.close()
		return [self._to_risk_indicator(d) for d in all_data]

	def _to_risk_indicator(self, indicator):
		su_repo = SpatialUnitDynamicMapperFactory.instance().\
							create_spatial_unit(self._spatial_unit_tablename,
												self._spatial_unit_as_attribute_name)
		sufeat = su_repo.get_feature(indicator.suid)
		# TODO: get alerts with intersection
		return RiskIndicator(indicator.date, indicator.percentage, indicator.classname, sufeat)		

	def save(self, indicators):
		session = self._dataaccess.create_session()
		for i in indicators:
			ri = SpatialUnitDynamicMapperFactory.instance().\
							create_risk_indicator(self._spatial_unit_tablename)
			ri.percentage = i.percentage
			ri.date = i.date
			ri.classname = i.classname
			ri.suid = i.feature.id
			session.add(ri)
		session.commit()
		session.close()

	def delete(self, from_date: datetime.date):
		session = self._dataaccess.create_session()
		riclass = SpatialUnitDynamicMapperFactory.instance().\
						risk_indicator_class(self._spatial_unit_tablename)
		session.query(riclass).filter(riclass.date >= from_date).\
								delete()
		session.commit() 		

	def get_most_recent(self) -> RiskIndicator:
		session = self._dataaccess.create_session()
		riclass = SpatialUnitDynamicMapperFactory.instance().\
						risk_indicator_class(self._spatial_unit_tablename)		
		last = session.query(riclass).order_by(desc('date')).first()
		rilast = self._to_risk_indicator(last)
		session.close()
		return rilast
