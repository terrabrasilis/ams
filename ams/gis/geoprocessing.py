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

	def percentage_of_area(self, geom_ref: Geometry, geom_over: Geometry) -> float:
		return (geom_ref.intersection(geom_over).area / geom_ref.area) * 100

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
