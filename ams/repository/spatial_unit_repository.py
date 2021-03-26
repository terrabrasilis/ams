from sqlalchemy.orm import sessionmaker, scoped_session
from geoalchemy2.shape import to_shape
from ams.domain.entities import SpatialUnitFeature, SpatialUnit
from ams.gis import ShapelyGeometry


class SpatialUnitRepository:
	"""SpatialUnitRepository"""

	def __init__(self, tablename, engine):
		self._tablename = tablename
		self._engine = engine

	def _add_features(self):
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		all_data = session.query(self.__class__).all()
		session.close()
		for d in all_data:
			feat = self._to_su_feature(d) 
			self._spatial_unit.add(feat)

	def get(self) -> SpatialUnit:
		self._spatial_unit = SpatialUnit(self._tablename)
		self._add_features()		
		return self._spatial_unit

	def get_feature(self, suid) -> SpatialUnitFeature:
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		feat = session.query(self.__class__).get(suid)
		session.close()
		return self._to_su_feature(feat)		

	def list(self) -> 'list[SpatialUnitFeature]':
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		all_data = session.query(self.__class__).all()
		session.close()
		return [self._to_su_feature(d) for d in all_data]		

	def _to_su_feature(self, dat) -> SpatialUnitFeature:
		geom = ShapelyGeometry(to_shape(dat.geometry))
		return SpatialUnitFeature(dat.suid, dat.id, geom)
