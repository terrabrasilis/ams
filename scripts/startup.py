import os
import datetime
from ams.dataaccess import AlchemyDataAccess
from ams.gis import Geoprocessing
from ams.usecases import AddSpatialUnit, DetermineRiskIndicators
from ams.repository import (SpatialUnitDynamicMapperFactory, SpatialUnitInfoRepository,
							DeterClassGroupRepository, DeterRepository,
							DeterHistoricalRepository, RiskIndicatorsRepository)
from ams.domain.entities import DeterClassGroup


def setdb(url):
	db = AlchemyDataAccess()
	db.connect(url)
	db.create_all(True)
	db.add_postgis_extension()
	SpatialUnitDynamicMapperFactory.instance().dataaccess = db
	return db 


def set_spatial_units(db):	
	data_path = os.path.join(os.path.dirname(__file__), '../data')
	sus = [
		{'tablename': 'csAmz_150km', 
			'shpfile': f'{data_path}/csAmz_150km_epsg_4326.shp', 
			'as_attribute_name': 'id'},
		{'tablename': 'csAmz_300km', 
			'shpfile': f'{data_path}/csAmz_300km_epsg_4326.shp', 
			'as_attribute_name': 'id'},
		{'tablename': 'amz_states', 
			'shpfile': f'{data_path}/amz_states_epsg_4326.shp', 
			'as_attribute_name': 'NM_ESTADO'},
		{'tablename': 'amz_municipalities', 
			'shpfile': f'{data_path}/amz_municipalities_epsg_4326.shp', 
			'as_attribute_name': 'nm_municip'}
	]
	gp = Geoprocessing()
	sus_info_repo = SpatialUnitInfoRepository(db)
	for su in sus:
		uc = AddSpatialUnit(su['tablename'], su['shpfile'], su['as_attribute_name'],
						sus_info_repo, SpatialUnitDynamicMapperFactory.instance(), gp)		
		uc.execute(db)


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
	deter_hist = DeterHistoricalRepository()
	startdate = datetime.datetime.now().date()
	enddate = datetime.date(2017, 1, 1)
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
		uc = DetermineRiskIndicators(su, deter_alerts, deter_hist, class_groups, startdate, enddate)	
		model_indicators = uc.execute()
		rirepo = RiskIndicatorsRepository(sutablename, db)
		rirepo.save(model_indicators)	


db = setdb('postgresql://postgres:postgres@localhost:5432/AMS')
set_spatial_units(db)
set_class_groups(db)
determine_risk_indicators(db)
