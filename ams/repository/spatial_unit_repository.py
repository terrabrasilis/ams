from sqlalchemy import (MetaData, Table, Column, ForeignKey, 
						Integer, String)
from sqlalchemy.orm import mapper, relationship, class_mapper
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from ams.domain.entities import SpatialUnitFeature, SpatialUnit
from ams.gis import ShapelyGeometry
#from .risk_indicators_repository import RiskIndicatorsRepository


class SpatialUnitRepository:
	"""SpatialUnitRepository"""

	def __init__(self, tablename, engine):
		self._tablename = tablename
		self._engine = engine

	def create_table(self):
		metadata = MetaData()
		#metadata.reflect(bind=self._engine)
		#table = metadata.tables.get(self._tablename)
		#if table is None:
		# 	metadata.remove(table)
		table = Table(self._tablename, metadata,
			Column('suid', Integer, primary_key=True),
			autoload=True, 
			autoload_with=self._engine
		)
		try:	
			class_mapper(self.__class__)
		except UnmappedClassError:
			mapper(self.__class__, table)	
		metadata.create_all(bind=self._engine)
		# mapper(self.__class__, table, properties={
		# 	'su': relationship(RiskIndicatorsRepository, uselist=False)
		# })
		#self._engine = engine
		self._spatial_unit = SpatialUnit(self._tablename)
		self._add_features()

	def _add_features(self):
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		all_data = session.query(self.__class__).all()
		session.close()
		for d in all_data:
			feat = self._to_su_feature(d) 
			self._spatial_unit.add(feat)

	def get(self) -> SpatialUnit:
		return self._spatial_unit

	def get_feature(self, suid) -> SpatialUnitFeature:
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		feat = session.query(self.__class__).get(suid)
		session.close()
		return self._to_su_feature(feat)		

	def list(self):
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		all_data = session.query(self.__class__).all()
		session.close()
		return [self._to_su_feature(d) for d in all_data]		

	def _to_su_feature(self, dat) -> SpatialUnitFeature:
		geom = ShapelyGeometry(to_shape(dat.geometry))
		return SpatialUnitFeature(dat.suid, dat.id, geom)
