import geopandas


class Geoprocessing:
	"""docstring for Geoprocessing"""
	# def __init__(self, arg):
		# super(Geoprocessing, self).__init__()
		# self.arg = arg
	def export_shp_to_postgis(self, filepath: str, tablename: str, 
							id_label: str, engine, overwrite: bool):
		shp = geopandas.read_file(filepath)
		shp.to_postgis(tablename, engine, 
					if_exists='replace' if overwrite else None,
					index=True, index_label=id_label)