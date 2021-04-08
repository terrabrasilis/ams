import geopandas
import fiona
from ams.domain.entities import Geometry, Centroid


class Geoprocessing:
	"""Geoprocessing"""

	def export_shp_to_postgis(self, filepath: str, tablename: str, 
							id_label: str, engine, overwrite: bool):
		shp = geopandas.read_file(filepath)
		shp.to_postgis(tablename, engine, 
					if_exists='replace' if overwrite else None,
					index=True, index_label=id_label)	

	def percentage_of_area(self, geomA: Geometry, geomB: Geometry) -> float:
		return (geomA.intersection(geomB).area / geomA.area) * 100

	def centroid(self, filepath: str) -> Centroid:
		shp = fiona.open(filepath)
		bbox = shp.bounds
		minx = bbox[0]
		miny = bbox[1]
		maxx = bbox[2]
		maxy = bbox[3]
		cx = (minx + maxx) / 2
		cy = (miny + maxy) / 2
		return Centroid(cy, cx)