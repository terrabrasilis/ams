import os
import datetime
import sys
from ams.dataaccess import AlchemyDataAccess
from ams.gis import Geoprocessing
from ams.repository import (DeterRepository, RiskIndicatorsRepository, 
							SpatialUnitDynamicMapperFactory)
from ams.usecases import DetermineRiskIndicators


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data import determine_risk_indicators_result  # noqa: E402


def test_uc():
	url = 'postgresql://postgres:postgres@localhost:5432/det_risk_uc'
	db = AlchemyDataAccess()
	db.connect(url)
	db.create(True)
	db.add_postgis_extension()
	sutablename = 'csAmz_150km'
	shpfilepath = os.path.join(os.path.dirname(__file__), '../data', 'csAmz_150km_epsg_4326.shp')	
	geoprocess = Geoprocessing()
	geoprocess.export_shp_to_postgis(shpfilepath, sutablename, 'suid', db.engine, True)
	SpatialUnitDynamicMapperFactory.instance().dataaccess = db
	SpatialUnitDynamicMapperFactory.instance().add_class_mapper(sutablename)	
	surepo = SpatialUnitDynamicMapperFactory.instance().create_spatial_unit(sutablename)
	su = surepo.get()
	deter_alerts = DeterRepository()
	startdate = datetime.date(2021, 1, 1)
	enddate = datetime.date(2020, 12, 1)
	uc = DetermineRiskIndicators(su, deter_alerts, startdate, enddate)
	model_indicators = uc.execute()
	rirepo = RiskIndicatorsRepository(sutablename, db)
	rirepo.save(model_indicators)
	indicators = rirepo.list()
	indicators_per_feature = {}
	expected_total_per_feature = determine_risk_indicators_result.total_per_feature
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
	expected_per_day = determine_risk_indicators_result.percentage_per_day
	for i in range(len(indicators)):
		# print(f'{{\'id\': {i.feature.id}, \'percentage\': {i.percentage}, \'date\': \'{i.date}\'}},')
		assert expected_per_day[i]['id'] == indicators[i].feature.id
		assert round(expected_per_day[i]['percentage'], 5) == round(indicators[i].percentage, 5)
		assert expected_per_day[i]['date'] == str(indicators[i].date)
	db.drop()
