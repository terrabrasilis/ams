from sqlalchemy import (MetaData, Table, Column, ForeignKey, 
						Integer, String, Float, Date)
from sqlalchemy.orm import mapper, sessionmaker, scoped_session, relationship
from ams.domain.entities import RiskIndicator
from .spatial_unit_repository import SpatialUnitRepository


class RiskIndicatorsRepository:
	"""RiskIndicatorsRepository"""

	def __init__(self, spatial_unit_tablename: str, engine):
		self._engine = engine
		self._spatial_unit_tablename = spatial_unit_tablename
		self._tablename = f'{spatial_unit_tablename}_risk_indicators'

	def create_table(self):
		metadata = MetaData()
		metadata.reflect(bind=self._engine)
		table = metadata.tables.get(self._tablename)
		if table is None:
			table = Table(self._tablename, metadata,
				Column('id', Integer, primary_key=True, autoincrement=True),
				Column('percentage', Float),
				Column('date', Date),
				Column('suid', Integer, ForeignKey(f'{self._spatial_unit_tablename}.suid'), nullable=False),
			)		
			# TODO
			# mapper(SpatialUnitRepository, spatial_unit_table, properties={
			#  	'indicators': relationship(self.__class__, backref='su')
			# })
			# SpatialUnitRepository.indicator = relationship(self.__class__, backref='su')
			mapper(self.__class__, table) #, properties={
			#	'su': relationship(SpatialUnitRepository, primaryjoin=SpatialUnitRepository.suid==self.__class__.suid)
			#})
			metadata.create_all(bind=self._engine)

	def list(self) -> 'list[RiskIndicator]':
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		all_data = session.query(self.__class__).all()
		session.close()
		return [self._to_risk_indicator(d) for d in all_data]

	def _to_risk_indicator(self, indicator):
		su_repo = SpatialUnitRepository(self._spatial_unit_tablename, self._engine)
		su = su_repo.get_feature(indicator.suid)
		# TODO: get alerts with intersection
		return RiskIndicator(indicator.date, indicator.percentage, su, None)		

	def save(self, indicators):
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		for i in indicators:
			this = RiskIndicatorsRepository(self._tablename, self._engine)
			this.percentage = i.percentage
			this.date = i.date
			this.suid = i.feature.id
			session.add(this)
		session.commit()
		session.close()


