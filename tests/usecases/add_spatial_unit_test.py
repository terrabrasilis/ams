import os
from ams.dataaccess import AlchemyDataAccess
from ams.gis import Geoprocessing
from ams.repository import SpatialUnitInfoRepository, SpatialUnitDynamicMapperFactory
from ams.usecases import AddSpatialUnit


def test_add_two_spatial_units():
	url = 'postgresql://postgres:postgres@localhost:5432/two_sus'
	db = AlchemyDataAccess()
	db.connect(url)
	db.create(True)
	db.add_postgis_extension()
	db.create_all_tables()
	SpatialUnitDynamicMapperFactory.instance().dataaccess = db
	tablename1 = 'csAmz_150km'
	tablename2 = 'csAmz_300km'
	as_attribute_name = 'id'
	shpfilepath1 = os.path.join(os.path.dirname(__file__), 
								'../../data', 'csAmz_150km_epsg_4326.shp')
	shpfilepath2 = os.path.join(os.path.dirname(__file__), 
								'../../data', 'csAmz_300km_epsg_4326.shp')
	gp = Geoprocessing()
	sus1 = SpatialUnitInfoRepository(db)
	uc1 = AddSpatialUnit(tablename1, shpfilepath1, as_attribute_name,
					sus1, SpatialUnitDynamicMapperFactory.instance(), gp)
	uc2 = AddSpatialUnit(tablename2, shpfilepath2, as_attribute_name,
					sus1, SpatialUnitDynamicMapperFactory.instance(), gp)	
	su1 = uc1.execute(db)
	su2 = uc2.execute(db)
	sus2 = SpatialUnitInfoRepository(db)
	sus_list = sus2.list()
	assert len(sus_list) == 2
	assert sus_list[0].dataname == tablename1
	assert sus_list[1].dataname == tablename2
	assert sus_list[0].as_attribute_name == 'id'
	assert sus_list[1].as_attribute_name == 'id'
	assert sus_list[0].centroid.lat == -5.491382969006503
	assert sus_list[0].centroid.lng == -58.467185764253415
	assert sus_list[1].centroid.lat == -5.491382969006503
	assert sus_list[1].centroid.lng == -57.792239759933764	
	surepo1 = SpatialUnitDynamicMapperFactory.instance()\
				.create_spatial_unit(tablename1, as_attribute_name)
	surepo2 = SpatialUnitDynamicMapperFactory.instance()\
				.create_spatial_unit(tablename2, as_attribute_name)
	su1 = surepo1.get()
	su2 = surepo2.get()
	assert len(su1.features) == 240
	assert len(su2.features) == 70
	db.drop()


def test_as_attribute_name():
	url = 'postgresql://postgres:postgres@localhost:5432/as_attrname'
	db = AlchemyDataAccess()
	db.connect(url)
	db.create(True)
	db.add_postgis_extension()
	db.create_all_tables()
	SpatialUnitDynamicMapperFactory.instance().dataaccess = db
	tablename1 = 'amz_states'
	shpfilepath1 = os.path.join(os.path.dirname(__file__), '../../data', 'amz_states_epsg_4326.shp')
	as_attribute_name = 'NM_ESTADO'
	gp = Geoprocessing()
	sus1 = SpatialUnitInfoRepository(db)
	uc1 = AddSpatialUnit(tablename1, shpfilepath1, as_attribute_name,
					sus1, SpatialUnitDynamicMapperFactory.instance(), gp)
	su1 = uc1.execute(db)
	sus_list = sus1.list()
	assert len(sus_list) == 1
	assert sus_list[0].dataname == tablename1
	assert sus_list[0].as_attribute_name == 'NM_ESTADO'
	assert sus_list[0].centroid.lat == -6.384962796500002
	assert sus_list[0].centroid.lng == -58.97111531179317
	surepo1 = SpatialUnitDynamicMapperFactory.instance()\
				.create_spatial_unit(tablename1, as_attribute_name)
	su1 = surepo1.get()
	assert len(su1.features) == 13
	assert su1.features[0].name == 'ACRE'
	assert su1.features[1].name == 'AMAPÁ'
	db.drop()
