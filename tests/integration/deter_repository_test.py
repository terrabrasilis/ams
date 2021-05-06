import datetime
from ams.repository import DeterRepository


def test_list_all():
	deter = DeterRepository()
	alerts = deter.list()
	assert len(alerts) == 111158
	assert alerts[0].date.isoformat() == '2021-02-28'
	assert alerts[-1].date.isoformat() == '2020-01-01'


def test_list_period():
	deter = DeterRepository()
	startdate = datetime.date(2021, 1, 1)
	enddate = datetime.date(2020, 12, 1)
	alerts = deter.list(start=startdate, end=enddate)
	assert len(alerts) == 2216
	assert alerts[0].date == startdate
	assert alerts[-1].date == enddate


def test_list_one_day():
	deter = DeterRepository()
	startdate = datetime.date(2021, 1, 1)
	alerts = deter.list(start=startdate, end=startdate)
	assert len(alerts) == 50
	assert alerts[0].date == startdate
	assert alerts[-1].date == startdate	
