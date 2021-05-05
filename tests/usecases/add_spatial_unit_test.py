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
	shpfilepath1 = os.path.join(os.path.dirname(__file__), '../../data', 'csAmz_150km_epsg_4326.shp')
	shpfilepath2 = os.path.join(os.path.dirname(__file__), '../../data', 'csAmz_300km_epsg_4326.shp')
	gp = Geoprocessing()
	sus1 = SpatialUnitInfoRepository(db)
	uc1 = AddSpatialUnit(tablename1, shpfilepath1, sus1, 
		SpatialUnitDynamicMapperFactory.instance(), gp)
	uc2 = AddSpatialUnit(tablename2, shpfilepath2, sus1, 
		SpatialUnitDynamicMapperFactory.instance(), gp)	
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
	surepo1 = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit(tablename1)
	surepo2 = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit(tablename2)
	su1 = surepo1.get()
	su2 = surepo2.get()
	assert len(su1.features) == 240
	assert len(su2.features) == 70
