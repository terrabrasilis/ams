import datetime
from ams.usecases import GetConfig
from tests.helpers.dataaccess_helper import DataAccessHelper


def test_basic():
	da = DataAccessHelper.createdb('postgresql://postgres:postgres@localhost:5432/get_config')
	DataAccessHelper.add_class_groups(da)
	susdata = [{'tablename': 'csAmz_150km', 
				'shpname': 'csAmz_150km_epsg_4326', 
				'as_attribute_name': 'id'},
				{'tablename': 'amz_states', 
				'shpname': 'amz_states_epsg_4326', 
				'as_attribute_name': 'NM_ESTADO'}]
	for sudata in susdata:
		DataAccessHelper.add_spatial_unit(da, sudata['tablename'], 
							sudata['shpname'], sudata['as_attribute_name'])
	startdate = datetime.date(2021, 2, 10)
	enddate = datetime.date(2021, 2, 1)
	DataAccessHelper.determine_risk_indicators(da, startdate, enddate)		
	uc = GetConfig()
	config = uc.execute(da) 
	print(config.spatial_units_info[0])
	assert len(config.spatial_units_info) == 2
	sus_info = config.spatial_units_info
	assert sus_info[0].dataname == 'csAmz_150km'
	assert sus_info[0].as_attribute_name == 'id'
	assert sus_info[0].centroid.lat == -5.491382969006503
	assert sus_info[0].centroid.lng == -58.467185764253415
	assert sus_info[1].dataname == 'amz_states'
	assert sus_info[1].as_attribute_name == 'NM_ESTADO'
	assert sus_info[1].centroid.lat == -6.384962796500002
	assert sus_info[1].centroid.lng == -58.97111531179317	
	class_groups = config.deter_class_groups
	assert class_groups[0].name == 'DG'
	assert class_groups[1].name == 'DS'
	assert class_groups[2].name == 'CS'
	assert len(class_groups[0]._classes) == 2
	assert len(class_groups[1]._classes) == 3
	assert len(class_groups[2]._classes) == 2
	dg_classes = class_groups[0]._classes
	ds_classes = class_groups[1]._classes
	cs_classes = class_groups[2]._classes
	assert dg_classes[0] == 'CICATRIZ_DE_QUEIMADA'
	assert dg_classes[1] == 'DEGRADACAO'
	assert ds_classes[0] == 'MINERACAO'
	assert ds_classes[1] == 'DESMATAMENTO_CR'
	assert ds_classes[2] == 'DESMATAMENTO_VEG'
	assert cs_classes[0] == 'CS_DESORDENADO'
	assert cs_classes[1] == 'CS_GEOMETRICO'
	assert len(config.most_recent_risk_indicators) == 2
	most_recent_ris = config.most_recent_risk_indicators
	assert most_recent_ris['csAmz_150km'].date.isoformat() == '2021-02-10'
	assert most_recent_ris['csAmz_150km'].classname == 'DS'
	assert most_recent_ris['csAmz_150km'].area == 0.06311452651477815
	assert most_recent_ris['csAmz_150km'].percentage == 0.00028050900673121164
	assert most_recent_ris['amz_states'].date.isoformat() == '2021-02-10'
	assert most_recent_ris['amz_states'].classname == 'DS'
	assert most_recent_ris['amz_states'].area == 0.3271273341033477
	assert most_recent_ris['amz_states'].percentage == 2.0839709659236244e-05
