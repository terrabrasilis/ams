from ams.dataaccess import AlchemyDataAccess
from ams.repository import DeterRepository


def test_read():
	deter = DeterRepository()
	alerts = deter.list()
	assert len(alerts) == 175085
	assert alerts[0]['classname'] == 'DESMATAMENTO_CR'
	assert alerts[-1]['classname'] == 'MINERACAO'
