from sqlalchemy.orm import sessionmaker, scoped_session
from ams.domain.entities import RiskIndicator
from ams.dataaccess import DataAccess
from .spatial_unit_dynamic_mapper_factory import SpatialUnitDynamicMapperFactory


class RiskIndicatorsRepository:
	"""RiskIndicatorsRepository"""

	def __init__(self, spatial_unit_tablename: str, dataaccess: DataAccess):
		self._dataaccess = dataaccess
		self._engine = dataaccess.engine
		self._spatial_unit_tablename = spatial_unit_tablename
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
							create_spatial_unit(self._spatial_unit_tablename)
		su = su_repo.get_feature(indicator.suid)
		# TODO: get alerts with intersection
		return RiskIndicator(indicator.date, indicator.percentage, su, None)		

	def save(self, indicators):
		session = self._dataaccess.create_session()
		for i in indicators:
			ri = SpatialUnitDynamicMapperFactory.instance().\
							create_risk_indicator(self._spatial_unit_tablename)
			ri.percentage = i.percentage
			ri.date = i.date
			ri.suid = i.feature.id
			session.add(ri)
		session.commit()
		session.close()
