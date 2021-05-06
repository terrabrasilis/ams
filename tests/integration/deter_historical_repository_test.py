import datetime
from ams.repository import DeterHistoricalRepository


def test_list_all():
	deter = DeterHistoricalRepository()
	alerts = deter.list()
	assert len(alerts) == 63927
	assert alerts[0].date.isoformat() == '2019-12-31'
	assert alerts[-1].date.isoformat() == '2019-08-01'	


def test_list_period():
	deter = DeterHistoricalRepository()
	startdate = datetime.date(2019, 9, 1)
	enddate = datetime.date(2019, 8, 1)
	alerts = deter.list(start=startdate, end=enddate)
	assert len(alerts) == 27171
	assert alerts[0].date == startdate
	assert alerts[-1].date == enddate


def test_list_one_day():
	deter = DeterHistoricalRepository()
	startdate = datetime.date(2019, 8, 1)
	alerts = deter.list(start=startdate, end=startdate)
	assert len(alerts) == 533
	assert alerts[0].date == startdate
	assert alerts[-1].date == startdate	
