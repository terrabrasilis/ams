import os
from ams.dataaccess import AlchemyDataAccess
from ams.repository import DeterRepository
from ams.gis import Geoprocessing
from ams.repository import SpatialUnitDynamicMapperFactory


def test_export_shp_to_postgis():
	url = 'postgresql://postgres:postgres@localhost:5432/shp_to_postgis'
	db = AlchemyDataAccess()
	db.connect(url)
	db.create(True)
	db.add_postgis_extension()
	shpfilepath = os.path.join(os.path.dirname(__file__), '../data', 'csAmz_150km_epsg_4326.shp')
	geoprocess = Geoprocessing()
	geoprocess.export_shp_to_postgis(shpfilepath, 'csAmz_150km', 'suid', db.engine, True)
	SpatialUnitDynamicMapperFactory.instance().dataaccess = db
	SpatialUnitDynamicMapperFactory.instance().add_class_mapper('csAmz_150km')	
	sunit = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit('csAmz_150km')
	cells = sunit.list()
	assert len(cells) == 240
	assert cells[0].id == 0
	assert cells[-1].id == 239
	db.drop()


def test_percentage_of_area():
	url = 'postgresql://postgres:postgres@localhost:5432/percentage_of_area'
	db = AlchemyDataAccess()
	db.connect(url)
	db.create(True)
	db.add_postgis_extension()
	shpfilepath = os.path.join(os.path.dirname(__file__), '../data', 'csAmz_150km_epsg_4326.shp')
	geoprocess = Geoprocessing()
	geoprocess.export_shp_to_postgis(shpfilepath, 'csAmz_150km', 'suid', db.engine, True)
	SpatialUnitDynamicMapperFactory.instance().dataaccess = db
	SpatialUnitDynamicMapperFactory.instance().add_class_mapper('csAmz_150km')
	sunit = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit('csAmz_150km')	
	feats = sunit.list()
	deter = DeterRepository()
	a1 = deter.get(1)
	a1geom = a1.geom
	for f in feats:
		fgeom = f.geom
		if fgeom.intersects(a1geom):
			assert geoprocess.percentage_of_area(fgeom, a1geom) == 0.0005461506800423614
			assert geoprocess.percentage_of_area(a1geom, fgeom) == 100
			assert fgeom.intersection(a1geom).area == a1geom.area
	db.drop()
