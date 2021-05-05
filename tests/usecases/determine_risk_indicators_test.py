import os
import datetime
import sys
from ams.dataaccess import AlchemyDataAccess
from ams.gis import Geoprocessing
from ams.repository import (DeterRepository, 
							RiskIndicatorsRepository, 
							SpatialUnitDynamicMapperFactory, 
							DeterClassGroupRepository,
							SpatialUnitInfoRepository)
from ams.usecases import DetermineRiskIndicators, AddSpatialUnit
from ams.domain.entities import DeterClassGroup


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data import determine_risk_indicators_results  # noqa: E402


def test_uc_basic():	
	db = setdb('postgresql://postgres:postgres@localhost:5432/det_risk_uc_basic')
	units_repo = SpatialUnitInfoRepository(db)
	units = units_repo.list()
	sutablename = units[0].dataname
	surepo = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit(sutablename)
	su = surepo.get()	
	deter_alerts = DeterRepository()
	startdate = datetime.date(2021, 1, 1)
	enddate = datetime.date(2020, 12, 1)
	uc = DetermineRiskIndicators(su, deter_alerts, [], startdate, enddate)
	model_indicators = uc.execute()
	rirepo = RiskIndicatorsRepository(sutablename, db)
	rirepo.save(model_indicators)
	indicators = rirepo.list()
	indicators_per_feature = {}
	expected_total_per_feature = determine_risk_indicators_results.total_per_feature
	for ind in indicators:
		if ind.feature.id not in indicators_per_feature:
			indicators_per_feature[ind.feature.id] = 0	
		indicators_per_feature[ind.feature.id] += ind.percentage 
	assert len(model_indicators) == len(indicators) == 322
	assert (len(indicators_per_feature) 
			== len(expected_total_per_feature) 
			== 132)
	for i in range(len(expected_total_per_feature)):
		# print(f'{{\'id\': {i.feature.id}, \'percentage\': {i.percentage}}},')
		assert expected_total_per_feature[i]['id'] in indicators_per_feature
		assert (round(expected_total_per_feature[i]['percentage'], 5) 
				== round(indicators_per_feature[expected_total_per_feature[i]['id']], 5))
	expected_per_day = determine_risk_indicators_results.percentage_per_day
	for i in range(len(indicators)):
		# print(f'{{\'id\': {i.feature.id}, \'percentage\': {i.percentage}, \'date\': \'{i.date}\'}},')
		assert expected_per_day[i]['id'] == indicators[i].feature.id
		assert round(expected_per_day[i]['percentage'], 5) == round(indicators[i].percentage, 5)
		assert expected_per_day[i]['date'] == str(indicators[i].date)
	db.drop()


def test_uc_classes():
	db = setdb('postgresql://postgres:postgres@localhost:5432/det_risk_uc_classes')
	deter_alerts = DeterRepository()
	units_repo = SpatialUnitInfoRepository(db)
	units = units_repo.list()
	sutablename = units[0].dataname
	surepo = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit(sutablename)
	su = surepo.get()
	startdate = datetime.date(2021, 1, 1)
	enddate = datetime.date(2020, 12, 1)
	groups_repo = DeterClassGroupRepository(db)
	class_groups = groups_repo.list()
	uc = DetermineRiskIndicators(su, deter_alerts, class_groups, startdate, enddate)	
	model_indicators = uc.execute()
	rirepo = RiskIndicatorsRepository(sutablename, db)
	rirepo.save(model_indicators)
	indicators = rirepo.list()
	indicators_per_feature = {}
	expected_total_per_feature = determine_risk_indicators_results.total_per_feature
	for ind in indicators:
		if ind.feature.id not in indicators_per_feature:
			indicators_per_feature[ind.feature.id] = 0	
		indicators_per_feature[ind.feature.id] += ind.percentage 
	assert len(model_indicators) == len(indicators) == 424
	assert (len(indicators_per_feature) 
			== len(expected_total_per_feature) 
			== 132)
	for i in range(len(expected_total_per_feature)):
		# print(f'{{\'id\': {i.feature.id}, \'percentage\': {i.percentage}}},')
		assert expected_total_per_feature[i]['id'] in indicators_per_feature
		assert (round(expected_total_per_feature[i]['percentage'], 5) 
				== round(indicators_per_feature[expected_total_per_feature[i]['id']], 5))		
	# for i in indicators:
	# 	print(f'{{\'id\': {i.feature.id}, \'percentage\': {i.percentage},' 
	# 			+ f'\'classname\': \'{i.classname}\', \'date\': \'{i.date}\'}},')	
	expected_classname = determine_risk_indicators_results.percentage_classname
	for i in range(len(indicators)):
		assert expected_classname[i]['id'] == indicators[i].feature.id
		assert round(expected_classname[i]['percentage'], 5) == round(indicators[i].percentage, 5)
		assert expected_classname[i]['date'] == str(indicators[i].date)
	db.drop()


def setdb(url):
	db = AlchemyDataAccess()
	db.connect(url)
	db.create_all(True)
	db.add_postgis_extension()
	set_spatial_units(db)
	set_class_groups(db)
	return db 


def set_spatial_units(db):	
	sutablename = 'csAmz_150km'
	shpfilepath = os.path.join(os.path.dirname(__file__), '../../data', 'csAmz_150km_epsg_4326.shp')	
	geoprocess = Geoprocessing()
	SpatialUnitDynamicMapperFactory.instance().dataaccess = db
	sunits = SpatialUnitInfoRepository(db)
	uc1 = AddSpatialUnit(sutablename, shpfilepath, sunits, 
			     SpatialUnitDynamicMapperFactory.instance(), geoprocess)
	uc1.execute(db)
	SpatialUnitDynamicMapperFactory.instance().add_class_mapper(sutablename)


def set_class_groups(db):
	group_dg = DeterClassGroup('DG')
	group_dg.add_class('CICATRIZ_DE_QUEIMADA')
	group_dg.add_class('DEGRADACAO')
	group_ds = DeterClassGroup('DS')
	group_ds.add_class('MINERACAO')
	group_ds.add_class('DESMATAMENTO_CR')
	group_ds.add_class('DESMATAMENTO_VEG')
	group_cs = DeterClassGroup('CS')
	group_cs.add_class('CS_DESORDENADO')
	group_cs.add_class('CS_GEOMETRICO')
	group_repo = DeterClassGroupRepository(db)
	group_repo.add(group_dg)	
	group_repo.add(group_ds)	
	group_repo.add(group_cs)	
