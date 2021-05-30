from ams.dataaccess import DataAccess
from ams.entities import SpatialUnitInfo
from ams.repository import (SpatialUnitInfoRepository, 
							SpatialUnitDynamicMapperFactory)
from ams.gis import Geoprocessing


class AddSpatialUnit:
	"""AddSpatialUnit"""
	def __init__(self, tablename: str, 
				shpfilepath: str,
				as_attribute_name: str,
				sunits_repo: SpatialUnitInfoRepository, 
				su_dynamic_factory: SpatialUnitDynamicMapperFactory,
				geoprocessing: Geoprocessing):
		self._tablename = tablename
		self._shpfilepath = shpfilepath
		self._as_attribute_name = as_attribute_name
		self._sunits_repo = sunits_repo
		self._su_dynamic_factory = su_dynamic_factory
		self._geoprocessing = geoprocessing

	def execute(self, da: DataAccess) -> SpatialUnitInfo:
		self._geoprocessing.export_shp_to_postgis(self._shpfilepath, 
					self._tablename, 'suid', da.engine, True)	
		self._add_suid(da.engine)
		self._su_dynamic_factory.add_class_mapper(self._tablename)
		centroid = self._geoprocessing.centroid(self._shpfilepath)
		suinfo = SpatialUnitInfo(self._tablename, self._as_attribute_name, centroid)
		self._sunits_repo.add(suinfo)

	def _add_suid(self, engine):
		with engine.connect() as con:
			con.execute('commit')
			con.execute(f'ALTER TABLE "{self._tablename}" ADD PRIMARY KEY ("suid");')			
