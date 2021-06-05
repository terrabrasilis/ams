from contextlib import contextmanager
from flask import template_rendered
import os
import datetime
from ams.dataaccess import AlchemyDataAccess
from ams.gis import Geoprocessing
from ams.usecases import AddSpatialUnit, DetermineRiskIndicators
from ams.repository import (SpatialUnitDynamicMapperFactory, SpatialUnitInfoRepository,
                            DeterClassGroupRepository, DeterRepository,
                            RiskIndicatorsRepository)
from ams.entities import DeterClassGroup
from webapp.app.config import Config


class TestConfig(Config):
	TESTING = True
	DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/ams_webapp'	


# https://stackoverflow.com/questions/39822265/flask-testing-how-to-retrieve-variables-that-were-passed-to-jinja
@contextmanager
def get_context_variables(app):
    recorded = []
    
    def record(sender, template, context, **extra):
        recorded.append(context)
    template_rendered.connect(record, app)
    try:
        yield iter(recorded)
    finally:
        template_rendered.disconnect(record, app)   


def setdb(url):
    db = AlchemyDataAccess()
    db.connect(url)
    db.create_all(True)
    db.add_postgis_extension()
    SpatialUnitDynamicMapperFactory.instance().dataaccess = db
    return db 


def set_spatial_units(db):  
    tablename1 = 'csAmz_150km'
    tablename2 = 'csAmz_300km'
    shpfilepath1 = os.path.join(os.path.dirname(__file__), 
        '../../data', 'csAmz_150km_epsg_4326.shp')
    shpfilepath2 = os.path.join(os.path.dirname(__file__), 
        '../../data', 'csAmz_300km_epsg_4326.shp')
    as_attribute_name = 'id'
    gp = Geoprocessing()
    sus1 = SpatialUnitInfoRepository(db)
    uc1 = AddSpatialUnit(tablename1, shpfilepath1, as_attribute_name,
            sus1, SpatialUnitDynamicMapperFactory.instance(), gp)
    uc2 = AddSpatialUnit(tablename2, shpfilepath2, as_attribute_name,
            sus1, SpatialUnitDynamicMapperFactory.instance(), gp)     
    uc1.execute(db)
    uc2.execute(db)


def set_class_groups(db):
    group_ds = DeterClassGroup('DS')
    group_ds.add_class('DESMATAMENTO_CR')
    group_ds.add_class('DESMATAMENTO_VEG')
    group_dg = DeterClassGroup('DG')
    group_dg.add_class('CICATRIZ_DE_QUEIMADA')
    group_dg.add_class('DEGRADACAO')    
    group_cs = DeterClassGroup('CS')
    group_cs.add_class('CS_DESORDENADO')
    group_cs.add_class('CS_GEOMETRICO')
    group_mn = DeterClassGroup('MN')
    group_mn.add_class('MINERACAO')
    group_repo = DeterClassGroupRepository(db)
    group_repo.add(group_ds)    
    group_repo.add(group_dg)        
    group_repo.add(group_cs)    
    group_repo.add(group_mn)    


def determine_risk_indicators(db):
    deter_alerts = DeterRepository()
    startdate = datetime.date(2021, 2, 28)
    enddate = datetime.date(2020, 12, 31)
    groups_repo = DeterClassGroupRepository(db)
    class_groups = groups_repo.list()   
    units_repo = SpatialUnitInfoRepository(db)
    units = units_repo.list()
    for u in units:
        sutablename = u.dataname
        as_attribute_name = u.as_attribute_name
        surepo = SpatialUnitDynamicMapperFactory.instance()\
                    .create_spatial_unit(sutablename, as_attribute_name)
        su = surepo.get()   
        uc = DetermineRiskIndicators(su, deter_alerts, None, class_groups, startdate, enddate)  
        model_indicators = uc.execute()
        rirepo = RiskIndicatorsRepository(sutablename, as_attribute_name, db)
        rirepo.save(model_indicators)   
