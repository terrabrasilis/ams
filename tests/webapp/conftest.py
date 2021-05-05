import pytest
from webapp.app import create_app  
import appconftest
from appconftest import TestConfig


@pytest.fixture(scope="module")
def app_startup():
	db = appconftest.setdb('postgresql://postgres:postgres@localhost:5432/ams_webapp')
	appconftest.set_spatial_units(db)
	appconftest.set_class_groups(db)
	appconftest.determine_risk_indicators(db)
	yield
	db.drop()


@pytest.fixture
def app():
    app = create_app(TestConfig)
    return app		
