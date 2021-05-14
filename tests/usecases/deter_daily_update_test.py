import time
from datetime import datetime, date
from datetime import timedelta
from ams.usecases import DeterDailyUpdate
from ams.repository import (DeterRepository,
							RiskIndicatorsRepository)
from tests.helpers.dataaccess_helper import DataAccessHelper


def test_basic(mocker):
	db = DataAccessHelper.createdb('postgresql://postgres:postgres@localhost:5432/det_auto_up')
	DataAccessHelper.add_class_groups(db)
	susdata = [{'tablename': 'csAmz_150km', 'shpname': 'csAmz_150km_epsg_4326'}]
	for sudata in susdata:
		DataAccessHelper.add_spatial_unit(db, sudata['tablename'], sudata['shpname'])
	startdate = date(2021, 2, 28)
	enddate = date(2021, 1, 1)
	DataAccessHelper.determine_risk_indicators(db, startdate, enddate)
	deter_repo = DeterRepository()
	date_now = datetime.now()
	at = (date_now + timedelta(minutes=1)).strftime('%H:%M')
	deter_url = 'postgresql://postgres:postgres@localhost:5432/DETER-B'
	DataAccessHelper.del_deter_data(deter_url, date_now)
	rirepo = RiskIndicatorsRepository(susdata[0]['tablename'], db)	
	indicators_1 = rirepo.list()
	assert len(indicators_1) == 357
	assert indicators_1[0].date.isoformat() == '2021-02-28'
	assert indicators_1[0].percentage == 0.0004478673808316384
	assert indicators_1[0].classname == 'DS'
	uc = DeterDailyUpdate(deter_repo, at)
	mocker.patch.object(DeterDailyUpdate, '_get_enddate', return_value=date(2021, 1, 1))
	uc.execute(db)
	assert uc.last_update() == '2021-02-28'
	DataAccessHelper.add_deter_data(deter_url, 5, date_now)
	while uc.last_update() == '2021-02-28':
		time.sleep(1)	
	uc.terminate()	
	assert uc.last_update() == date_now.date().isoformat()
	indicators_2 = rirepo.list()
	assert len(indicators_2) == 358	
	now_indicator = get_newest_indicator(indicators_2, date_now.date())
	assert now_indicator.date.isoformat() == date_now.date().isoformat()
	assert round(now_indicator.percentage, 5) == round(0.0028141977493854964, 5)
	assert now_indicator.classname == 'DS'	
	DataAccessHelper.del_deter_data(deter_url, date_now)
	db.drop()


def get_newest_indicator(indicators, date):
	for ind in indicators:
		if ind.date == date:
			return ind
