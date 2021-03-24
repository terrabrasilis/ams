import os
import datetime
from ams.dataaccess import AlchemyDataAccess
from ams.gis import Geoprocessing
from ams.repository import (SpatialUnitRepository, DeterRepository,
							RiskIndicatorsRepository)
from ams.usecases import DetermineRiskIndicators


import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data import determine_risk_indicators_result


def test_uc():
	url = 'postgresql://postgres:postgres@localhost:5432/ams'
	db = AlchemyDataAccess()
	db.connect(url)
	db.create(True)
	db.add_postgis_extension()
	sutablename = 'csAmz_150km'
	shpfilepath = os.path.join(os.path.dirname(__file__), '../data', 'csAmz_150km_epsg_4326.shp')	
	geoprocess = Geoprocessing()
	geoprocess.export_shp_to_postgis(shpfilepath, sutablename, 'suid', db.engine, True)
	su_repo = SpatialUnitRepository(sutablename, db.engine)		
	ri_repo = RiskIndicatorsRepository(sutablename, db.engine)	
	su_repo.create_table()
	ri_repo.create_table()
	su = su_repo.get()
	deter_alerts = DeterRepository()
	startdate = datetime.date(2021, 1, 1)
	uc = DetermineRiskIndicators(su, deter_alerts, startdate)
	percentages = uc.execute()
	ri_repo.save(percentages)
	indicators = ri_repo.list()
	assert len(percentages) == len(indicators) == 132
	expected = determine_risk_indicators_result.result
	for i in range(len(indicators)):
		#print(f'{{\'id\': {i.feature.id}, \'percentage\': {i.percentage}}},')
		assert expected[i]['id'] == indicators[i].feature.id
		assert round(expected[i]['percentage'], 5) == round(indicators[i].percentage, 5)
	db.drop()