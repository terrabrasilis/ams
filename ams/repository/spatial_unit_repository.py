from geoalchemy2.shape import to_shape
from ams.domain.entities import SpatialUnitFeature, SpatialUnit
from ams.gis import ShapelyGeometry
from ams.dataaccess import DataAccess


class SpatialUnitRepository:
	"""SpatialUnitRepository"""

	def __init__(self, tablename: str, 
					as_attribute_name: str, 
					dataaccess: DataAccess):
		self._tablename = tablename
		self._as_attribute_name = as_attribute_name
		self._dataaccess = dataaccess
		self._engine = dataaccess.engine

	def _add_features(self):
		session = self._dataaccess.create_session()
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
		session = self._dataaccess.create_session()
		feat = session.query(self.__class__).get(suid)
		session.close()
		return self._to_su_feature(feat)		

	def list(self) -> 'list[SpatialUnitFeature]':
		session = self._dataaccess.create_session()
		all_data = session.query(self.__class__).all()
		session.close()
		return [self._to_su_feature(d) for d in all_data]		

	def _to_su_feature(self, dat) -> SpatialUnitFeature:
		geom = ShapelyGeometry(to_shape(dat.geometry))
		return SpatialUnitFeature(dat.suid, dat.__dict__[self._as_attribute_name], geom)
