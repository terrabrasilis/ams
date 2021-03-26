from ams.dataaccess import DataAccess
from ams.gis import Geoprocessing
from ams.domain.entities import SpatialUnit


class AddSpatialUnit:
	"""AddSpatialUnit"""
	def __init__(self, tablename: str, shpfilepath: str,
				geoprocessing):
		self._tablename = tablename
		self._shpfilepath = shpfilepath
		self._geoprocessing = geoprocessing

	def execute(self, da: DataAccess) -> SpatialUnit:
		self._geoprocessing.export_shp_to_postgis(self._shpfilepath, 
					self._tablename, 'suid', da.engine, True)
		return SpatialUnit(self._tablename)
		