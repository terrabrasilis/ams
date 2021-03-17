import os
from ams.dataaccess import AlchemyDataAccess
from ams.repository import SpatialUnitRepository, DeterRepository
from ams.gis import Geoprocessing
from shapely import wkb
from binascii import unhexlify
from geoalchemy2.shape import to_shape
from shapely.geometry.polygon import Polygon


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
	db.drop()

def test_percentage_of_area():
	url = 'postgresql://postgres:postgres@localhost:5432/ams'
	db = AlchemyDataAccess()
	db.connect(url)
	db.create(True)
	db.add_postgis_extension()
	shpfilepath = os.path.join(os.path.dirname(__file__), '../data', 'csAmz_150km_epsg_4326.shp')
	geoprocess = Geoprocessing()
	geoprocess.export_shp_to_postgis(shpfilepath, 'csAmz_150km', 'fid', db.engine, True)
	sunit = SpatialUnitRepository('csAmz_150km', db.engine)	
	cells = sunit.list()
	deter = DeterRepository()
	a1 = deter.get(1)
	for c in cells:
		if c['geom'].intersects(a1['geom']):
			assert geoprocess.percentage_of_area(c['geom'], a1['geom']) == 0.0005461506800423614
			assert geoprocess.percentage_of_area(a1['geom'], c['geom']) == 100
			assert c['geom'].intersection(a1['geom']).area == a1['geom'].area
	db.drop()
