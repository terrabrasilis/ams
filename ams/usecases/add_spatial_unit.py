from ams.dataaccess import DataAccess
from ams.domain.entities import SpatialUnitInfo
from ams.repository import SpatialUnitInfoRepository, SpatialUnitDynamicMapperFactory


class AddSpatialUnit:
	"""AddSpatialUnit"""
	def __init__(self, tablename: str, 
				shpfilepath: str,
				sunits_repo: SpatialUnitInfoRepository, 
				su_dynamic_factory: SpatialUnitDynamicMapperFactory,
				geoprocessing):
		self._tablename = tablename
		self._shpfilepath = shpfilepath
		self._sunits_repo = sunits_repo
		self._su_dynamic_factory = su_dynamic_factory
		self._geoprocessing = geoprocessing

	def execute(self, da: DataAccess) -> SpatialUnitInfo:
		self._geoprocessing.export_shp_to_postgis(self._shpfilepath, 
					self._tablename, 'suid', da.engine, True)	
		self._add_suid(da.engine)
		self._su_dynamic_factory.add_class_mapper(self._tablename)
		centroid = self._geoprocessing.centroid(self._shpfilepath)
		suinfo = SpatialUnitInfo(self._tablename, 'id', centroid)
		self._sunits_repo.add(suinfo)

	def _add_suid(self, engine):
		with engine.connect() as con:
			con.execute('commit')
			con.execute(f'ALTER TABLE "{self._tablename}" ADD PRIMARY KEY ("suid");')			
