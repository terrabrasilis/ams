import geopandas
from sqlalchemy import MetaData
from ams.domain.entities import Geometry


class Geoprocessing:
	"""Geoprocessing"""

	def export_shp_to_postgis(self, filepath: str, tablename: str, 
							id_label: str, engine, overwrite: bool):
		shp = geopandas.read_file(filepath)
		shp.to_postgis(tablename, engine, 
					if_exists='replace' if overwrite else None,
					index=True, index_label=id_label)
		with engine.connect() as con:
			con.execute('commit')
			con.execute(f'ALTER TABLE "{tablename}" ADD PRIMARY KEY ("{id_label}");')			

	def percentage_of_area(self, geomA: Geometry, geomB: Geometry) -> float:
		return (geomA.intersection(geomB).area/geomA.area)*100
