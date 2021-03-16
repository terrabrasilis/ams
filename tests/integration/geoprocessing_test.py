import os
from ams.dataaccess import AlchemyDataAccess
from ams.repository import SpatialUnitRepository
from ams.gis import Geoprocessing


def test_export_shp_to_postgis():
	url = 'postgresql://postgres:postgres@localhost:5432/ams'
	db = AlchemyDataAccess()
	db.connect(url)
	db.create(True)
	db.add_postgis_extension()
	shpfilepath = os.path.join(os.path.dirname(__file__), '../data', 'csAmz_150km_epsg_5880.shp')
	geoprocess = Geoprocessing()
	geoprocess.export_shp_to_postgis(shpfilepath, 'csAmz_150km', 'fid', db.engine, True)
	sunit = SpatialUnitRepository('csAmz_150km', db.engine)
	cells = sunit.list()
	assert len(cells) == 241
	assert cells[0]['fid'] == 0
	assert cells[-1]['fid'] == 240
