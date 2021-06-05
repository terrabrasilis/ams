import time
from datetime import datetime, date, timedelta
from ams.usecases import DeterDailyUpdate
from ams.repository import (DeterRepository,
							RiskIndicatorsRepository)
from tests.helpers.dataaccess_helper import DataAccessHelper


def test_two_times(mocker):
	db = DataAccessHelper.createdb('postgresql://postgres:postgres@localhost:5432/det_autoup')
	DataAccessHelper.add_class_groups(db)
	susdata = [{'tablename': 'csAmz_150km', 
				'shpname': 'csAmz_150km_epsg_4326', 
				'as_attribute_name': 'id'}]
	for sudata in susdata:
		DataAccessHelper.add_spatial_unit(db, sudata['tablename'], sudata['shpname'])
	startdate = date(2021, 2, 28)
	enddate = date(2021, 1, 1)
	DataAccessHelper.determine_risk_indicators(db, startdate, enddate)
	deter_repo = DeterRepository()
	deter_url = 'postgresql://postgres:postgres@localhost:5432/DETER-B'
	date_now = datetime.now()
	yesterday = (date_now - timedelta(days=1))	
	DataAccessHelper.del_deter_data(deter_url, date_now)  # clean if last test fail
	DataAccessHelper.del_deter_data(deter_url, yesterday)  # clean if last test fail
	rirepo = RiskIndicatorsRepository(susdata[0]['tablename'], susdata[0]['as_attribute_name'], db)	
	indicators_1 = rirepo.list()
	assert len(indicators_1) == 357
	assert indicators_1[0].date.isoformat() == '2021-02-28'
	assert indicators_1[0].percentage == 0.0004478673808316384
	assert indicators_1[0].area == 0.10077016068752663
	assert indicators_1[0].classname == 'DS'
	uc = DeterDailyUpdate(deter_repo, 1)
	mocker.patch.object(DeterDailyUpdate, '_get_enddate', return_value=date(2021, 1, 1))
	uc.execute(db)	
	assert uc.last_update() == '2021-02-28'
	DataAccessHelper.add_deter_data(deter_url, 5, yesterday)
	while uc.last_update() == startdate.isoformat():
		time.sleep(1)		
	assert uc.last_update() == yesterday.date().isoformat()
	indicators_2 = rirepo.list()
	assert len(indicators_2) == 358	
	yesterday_indicator = get_newest_indicator(indicators_2, yesterday.date())
	assert yesterday_indicator.date.isoformat() == yesterday.date().isoformat()
	assert round(yesterday_indicator.percentage, 5) == round(0.0028141977493854964, 5)
	assert round(yesterday_indicator.area, 5) == 0.63319
	assert yesterday_indicator.classname == 'DS'	
	DataAccessHelper.add_deter_data(deter_url, 5, date_now)
	while uc.last_update() == yesterday.date().isoformat():
		time.sleep(1)	
	assert uc.last_update() == date_now.date().isoformat()
	indicators_3 = rirepo.list()
	assert len(indicators_3) == 359	
	now_indicator = get_newest_indicator(indicators_3, date_now.date())
	assert now_indicator.date.isoformat() == date_now.date().isoformat()
	assert round(now_indicator.percentage, 5) == round(0.0028141977493854964, 5)
	assert round(now_indicator.area, 5) == 0.63319
	assert now_indicator.classname == 'DS'				
	uc.terminate()
	DataAccessHelper.del_deter_data(deter_url, yesterday)
	DataAccessHelper.del_deter_data(deter_url, date_now)
	db.drop()


def test_handle_exception(mocker):
	db = DataAccessHelper.createdb('postgresql://postgres:postgres@localhost:5432/det_autoup_exc')
	DataAccessHelper.add_class_groups(db)
	susdata = [{'tablename': 'csAmz_150km', 
				'shpname': 'csAmz_150km_epsg_4326', 
				'as_attribute_name': 'id'}]
	for sudata in susdata:
		DataAccessHelper.add_spatial_unit(db, sudata['tablename'], sudata['shpname'])
	startdate = date(2021, 2, 28)
	enddate = date(2021, 1, 1)
	DataAccessHelper.determine_risk_indicators(db, startdate, enddate)
	deter_repo = DeterRepository()
	deter_url = 'postgresql://postgres:postgres@localhost:5432/DETER-B'
	date_now = datetime.now()
	DataAccessHelper.del_deter_data(deter_url, date_now)  # clean if last test fail
	rirepo = RiskIndicatorsRepository(susdata[0]['tablename'], susdata[0]['as_attribute_name'], db)	
	indicators_1 = rirepo.list()
	assert len(indicators_1) == 357
	assert indicators_1[0].date.isoformat() == '2021-02-28'
	assert indicators_1[0].percentage == 0.0004478673808316384
	assert indicators_1[0].area == 0.10077016068752663
	assert indicators_1[0].classname == 'DS'
	uc = DeterDailyUpdate(deter_repo, 1)
	mocker.patch.object(DeterDailyUpdate, '_get_enddate', return_value="wrong return here!")
	uc.execute(db)	
	assert uc.last_update() == '2021-02-28'
	DataAccessHelper.add_deter_data(deter_url, 5, date_now)
	two_minutes = (date_now + timedelta(minutes=2))
	while uc.last_update() == startdate.isoformat():
		time.sleep(1)		
		if datetime.now().strftime('%H:%M') >= two_minutes.strftime('%H:%M'):
			mocker.patch.object(DeterDailyUpdate, '_get_enddate', return_value=date(2021, 1, 1))
	assert uc.last_update() == date_now.date().isoformat()
	indicators_2 = rirepo.list()
	assert len(indicators_2) == 358	
	yesterday_indicator = get_newest_indicator(indicators_2, date_now.date())
	assert yesterday_indicator.date.isoformat() == date_now.date().isoformat()
	assert round(yesterday_indicator.percentage, 5) == round(0.0028141977493854964, 5)
	assert round(yesterday_indicator.area, 5) == 0.63319
	assert yesterday_indicator.classname == 'DS'	
	uc.terminate()
	DataAccessHelper.del_deter_data(deter_url, date_now)
	db.drop()


def test_update_on_startup(mocker):
	db = DataAccessHelper.createdb('postgresql://postgres:postgres@localhost:5432/det_autoup_onstart')
	DataAccessHelper.add_class_groups(db)
	susdata = [{'tablename': 'csAmz_150km', 
				'shpname': 'csAmz_150km_epsg_4326', 
				'as_attribute_name': 'id'}]
	for sudata in susdata:
		DataAccessHelper.add_spatial_unit(db, sudata['tablename'], sudata['shpname'])
	startdate = date(2021, 2, 28)
	enddate = date(2021, 1, 1)
	DataAccessHelper.determine_risk_indicators(db, startdate, enddate)
	deter_repo = DeterRepository()
	deter_url = 'postgresql://postgres:postgres@localhost:5432/DETER-B'
	date_now = datetime.now()
	DataAccessHelper.del_deter_data(deter_url, date_now)  # clean if last test fail
	rirepo = RiskIndicatorsRepository(susdata[0]['tablename'], susdata[0]['as_attribute_name'], db)	
	indicators_1 = rirepo.list()
	assert len(indicators_1) == 357
	assert indicators_1[0].date.isoformat() == '2021-02-28'
	assert indicators_1[0].percentage == 0.0004478673808316384
	assert indicators_1[0].area == 0.10077016068752663
	assert indicators_1[0].classname == 'DS'
	DataAccessHelper.add_deter_data(deter_url, 5, date_now)
	uc = DeterDailyUpdate(deter_repo, 1)
	mocker.patch.object(DeterDailyUpdate, '_get_enddate', return_value=date(2021, 1, 1))
	uc.execute(db)
	assert uc.last_update() == date_now.date().isoformat()
	indicators_2 = rirepo.list()
	assert len(indicators_2) == 358	
	yesterday_indicator = get_newest_indicator(indicators_2, date_now.date())
	assert yesterday_indicator.date.isoformat() == date_now.date().isoformat()
	assert round(yesterday_indicator.percentage, 5) == round(0.0028141977493854964, 5)
	assert round(yesterday_indicator.area, 5) == 0.63319
	assert yesterday_indicator.classname == 'DS'	
	uc.terminate()
	DataAccessHelper.del_deter_data(deter_url, date_now)
	db.drop()


def get_newest_indicator(indicators, date):
	for ind in indicators:
		if ind.date == date:
			return ind
