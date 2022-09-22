import datetime
from sqlalchemy import desc
from ams.entities import RiskIndicator
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
		self._tablename = f'{spatial_unit_tablename}_land_use'

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
		return RiskIndicator(indicator.date, indicator.percentage, 
							indicator.area, indicator.classname, sufeat)		

	def save(self, indicators: 'list[RiskIndicator]'):
		session = self._dataaccess.create_session()
		count = 0
		for i in indicators:
			ri = SpatialUnitDynamicMapperFactory.instance().\
							create_risk_indicator(self._spatial_unit_tablename)
			ri.percentage = i.percentage
			ri.area = i.area
			ri.date = i.date
			ri.classname = i.classname
			ri.suid = i.feature.id
			session.add(ri)
			count += 1
			if count == 50:
				session.commit()
				count = 0
		session.commit()
		session.close()

	def overwrite_from_date(self, indicators: 'list[RiskIndicator]', 
							from_date: datetime.date):
		session = self._dataaccess.create_session()
		try:
			self._mark_to_delete(from_date)
			self._mark_to_add(session, indicators)
			session.commit()
		except Exception:
			session.rollback()
		session.close()		

	def _mark_to_add(self, session, indicators):
		for i in indicators:
			ri = SpatialUnitDynamicMapperFactory.instance().\
							create_risk_indicator(self._spatial_unit_tablename)
			ri.percentage = i.percentage
			ri.area = i.area
			ri.date = i.date
			ri.classname = i.classname
			ri.suid = i.feature.id
			session.add(ri)			

	def _mark_to_delete(self, from_date):
		session = self._dataaccess.create_session()
		riclass = SpatialUnitDynamicMapperFactory.instance().\
						risk_indicator_class(self._spatial_unit_tablename)
		session.query(riclass).filter(riclass.date >= from_date).delete()	

	def get_most_recent(self) -> RiskIndicator:
		session = self._dataaccess.create_session()
		riclass = SpatialUnitDynamicMapperFactory.instance().\
						risk_indicator_class(self._spatial_unit_tablename)		
		last = session.query(riclass).order_by(desc('date')).first()
		rilast = self._to_risk_indicator(last)
		session.close()
		return rilast
