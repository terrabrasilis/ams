import os
import datetime
from sqlalchemy import create_engine
from ams.dataaccess import DataAccess, AlchemyDataAccess
from ams.entities import DeterClassGroup
from ams.repository import (DeterClassGroupRepository,
							SpatialUnitDynamicMapperFactory,
							SpatialUnitInfoRepository,
							DeterRepository,
							RiskIndicatorsRepository)
from ams.gis import Geoprocessing
from ams.usecases import (AddSpatialUnit,
							DetermineRiskIndicators)


class DataAccessHelper:
	"""DataAccessHelper"""

	@staticmethod
	def createdb(url: str) -> DataAccess:
		db = AlchemyDataAccess()
		db.connect(url)
		db.create_all(True)
		db.add_postgis_extension()
		return db 

	@staticmethod
	def add_spatial_unit(db: DataAccess, sutablename: str = 'csAmz_150km', 
							shpfilename: str = 'csAmz_150km_epsg_4326',
							as_attribute_name: str = 'id'):	
		shpfilepath = os.path.join(os.path.dirname(__file__), '../../data', f'{shpfilename}.shp')	
		geoprocess = Geoprocessing()
		SpatialUnitDynamicMapperFactory.instance().dataaccess = db
		sunits = SpatialUnitInfoRepository(db)
		uc1 = AddSpatialUnit(sutablename, shpfilepath, as_attribute_name,
						sunits, SpatialUnitDynamicMapperFactory.instance(), geoprocess)
		uc1.execute(db)
		SpatialUnitDynamicMapperFactory.instance().add_class_mapper(sutablename)

	@staticmethod
	def add_class_groups(db: DataAccess):
		group_dg = DeterClassGroup('DG')
		group_dg.add_class('CICATRIZ_DE_QUEIMADA')
		group_dg.add_class('DEGRADACAO')
		group_ds = DeterClassGroup('DS')
		group_ds.add_class('MINERACAO')
		group_ds.add_class('DESMATAMENTO_CR')
		group_ds.add_class('DESMATAMENTO_VEG')
		group_cs = DeterClassGroup('CS')
		group_cs.add_class('CS_DESORDENADO')
		group_cs.add_class('CS_GEOMETRICO')
		group_repo = DeterClassGroupRepository(db)
		group_repo.add(group_dg)	
		group_repo.add(group_ds)	
		group_repo.add(group_cs)

	@staticmethod
	def determine_risk_indicators(db: DataAccess, 
									startdate: datetime.date, 
									enddate: datetime.date):
		deter_alerts = DeterRepository()
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
			uc = DetermineRiskIndicators(su, deter_alerts, [], class_groups, startdate, enddate)	
			model_indicators = uc.execute()
			rirepo = RiskIndicatorsRepository(sutablename, as_attribute_name, db)
			rirepo.save(model_indicators)	

	@staticmethod
	def add_deter_data(url: str, nrows: int, date: datetime.date):
		engine = create_engine(url)	
		with engine.connect() as con:
			con.execute('commit')
			hist = con.execute(
				f'SELECT * FROM public.deter_history ORDER BY date DESC LIMIT {nrows}')
			last = con.execute(
				'SELECT * FROM terrabrasilis.deter_table ORDER BY gid DESC LIMIT 1').fetchone()	
			gid = last['gid'] + 1
			values = ""
			count = 0
			for row in hist:
				values = values + (f'({gid}, {row["origin_gid"]}, \'{row["classname"]}\', \'\','
								+ f' {row["orbitpoint"]}, \'{date}\', \'{row["date_audit"]}\','
								+ f' {row["lot"]}, \'{row["sensor"]}\', \'{row["satellite"]}\', {row["areatotalkm"]} ,' 
								+ f' {row["areamunkm"]}, {row["areauckm"]}, \'{row["county"]}\', \'{row["uf"]}\', \'\','
								+ f' \'{row["geom"]}\', \'{row["publish_month"]}\', {row["geocod"]})')
				if count < nrows - 1:
					values = values + ','
				count += 1
				gid += 1
			con.execute('INSERT INTO terrabrasilis.deter_table(gid, origin_gid, classname, quadrant,'
						+ ' orbitpoint, date, date_audit, lot, sensor, satellite, areatotalkm, areamunkm,'
						+ ' areauckm, county, uf, uc, geom, publish_month, geocod)'
						+ f' VALUES {values}')

	@staticmethod
	def del_deter_data(url: str, date: datetime.date):
		engine = create_engine(url)	
		with engine.connect() as con:
			con.execute('commit')
			con.execute(f'DELETE FROM terrabrasilis.deter_table WHERE date=\'{date}\'')				
