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
	shpfilepath = os.path.join(os.path.dirname(__file__), '../../data', 'csAmz_150km_epsg_4326.shp')
	geoprocess = Geoprocessing()
	geoprocess.export_shp_to_postgis(shpfilepath, 'csAmz_150km', 'suid', db.engine, True)
	add_suid('csAmz_150km', db.engine)
	SpatialUnitDynamicMapperFactory.instance().dataaccess = db
	SpatialUnitDynamicMapperFactory.instance().add_class_mapper('csAmz_150km')	
	sunit = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit('csAmz_150km', 'id')
	cells = sunit.list()
	assert len(cells) == 240
	assert cells[0].id == 0
	assert cells[-1].id == 239
	db.drop()


def test_intersection_area():
	url = 'postgresql://postgres:postgres@localhost:5432/intersection_area'
	db = AlchemyDataAccess()
	db.connect(url)
	db.create(True)
	db.add_postgis_extension()
	shpfilepath = os.path.join(os.path.dirname(__file__), '../../data', 'csAmz_150km_epsg_4326.shp')
	geoprocess = Geoprocessing()
	geoprocess.export_shp_to_postgis(shpfilepath, 'csAmz_150km', 'suid', db.engine, True)
	add_suid('csAmz_150km', db.engine)
	SpatialUnitDynamicMapperFactory.instance().dataaccess = db
	SpatialUnitDynamicMapperFactory.instance().add_class_mapper('csAmz_150km')
	sunit = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit('csAmz_150km', 'id')	
	feats = sunit.list()
	deter = DeterRepository()
	a1 = deter.get(59241)
	a1geom = a1.geom
	for f in feats:
		fgeom = f.geom
		if fgeom.intersects(a1geom):
			area_info1 = geoprocess.intersection_area(fgeom, a1geom)
			area_info2 = geoprocess.intersection_area(a1geom, fgeom)
			assert area_info1['percentage'] == 0.001008271044465656
			assert area_info2['percentage'] == 100
			assert area_info1['area'] == area_info2['area'] == 0.22686098500569116
			assert fgeom.intersection(a1geom).area == a1geom.area
	db.drop()


def add_suid(tablename, engine):
	with engine.connect() as con:
		con.execute('commit')
		con.execute(f'ALTER TABLE "{tablename}" ADD PRIMARY KEY ("suid");')			
