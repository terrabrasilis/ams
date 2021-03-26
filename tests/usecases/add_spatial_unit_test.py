import os
from ams.dataaccess import AlchemyDataAccess
from ams.gis import Geoprocessing
from ams.repository import SpatialUnitsRepository, SpatialUnitDynamicMapperFactory
from ams.usecases import AddSpatialUnit


def test_add_two_spatial_units():
	url = 'postgresql://postgres:postgres@localhost:5432/two_sus'
	db = AlchemyDataAccess()
	db.connect(url)
	db.create(True)
	db.add_postgis_extension()
	db.create_all_tables()
	tablename1 = 'csAmz_150km'
	tablename2 = 'csAmz_300km'
	shpfilepath1 = os.path.join(os.path.dirname(__file__), '../data', 'csAmz_150km_epsg_4326.shp')
	shpfilepath2 = os.path.join(os.path.dirname(__file__), '../data', 'csAmz_300km_epsg_4326.shp')
	gp = Geoprocessing()
	uc1 = AddSpatialUnit(tablename1, shpfilepath1, gp)
	uc2 = AddSpatialUnit(tablename2, shpfilepath2, gp)	
	su1 = uc1.execute(db)
	su2 = uc2.execute(db)
	SpatialUnitDynamicMapperFactory.instance().engine = db.engine
	SpatialUnitDynamicMapperFactory.instance().add_class_mapper(tablename1)
	SpatialUnitDynamicMapperFactory.instance().add_class_mapper(tablename2)	
	sus1 = SpatialUnitsRepository(db.engine)
	sus1.add(su1, 'id')
	sus1.add(su2, 'id')
	sus2 = SpatialUnitsRepository(db.engine)
	sus_list = sus2.list()
	assert len(sus_list) == 2
	assert sus_list[0]['name'] == tablename1
	assert sus_list[1]['name'] == tablename2
	assert sus_list[1]['as_attribute_name'] == 'id'
	assert sus_list[1]['as_attribute_name'] == 'id'
	surepo1 = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit(tablename1)
	surepo2 = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit(tablename2)
	su1 = surepo1.get()
	su2 = surepo2.get()
	assert len(su1.features) == 240
	assert len(su2.features) == 70
