import datetime
from ams.repository import DeterRepository


def test_list():
	deter = DeterRepository()
	alerts = deter.list()
	assert len(alerts) == 111158
	assert alerts[0].date.isoformat() == '2020-02-01'
	assert alerts[-1].date.isoformat() == '2021-02-24'	
	assert alerts[0].classname == 'DESMATAMENTO_CR'
	assert alerts[-1].classname == 'MINERACAO'


def test_list_period():
	deter = DeterRepository()
	startdate = datetime.date(2021, 1, 1)
	enddate = datetime.date(2020, 12, 1)
	alerts = deter.list(start=startdate, end=enddate)
	assert len(alerts) == 2216
	assert alerts[0].date == startdate
	assert alerts[-1].date == enddate
