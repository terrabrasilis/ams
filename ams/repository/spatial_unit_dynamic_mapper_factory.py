from sqlalchemy import (MetaData, Table, Column, ForeignKey, 
						Integer, Float, Date, String)
from sqlalchemy.orm import mapper, relationship
from .spatial_unit_repository import SpatialUnitRepository
from .alchemy_orm import RiskIndicator


class SpatialUnitDynamicMapperFactory:
	"""SpatialUnitFactory"""
	_instance = None

	def __init__(self):
		self._types = {}
		self._dataaccess = None
		self._risk_indicator_suffix = '_risk_indicators'

	@classmethod
	def instance(cls):
		if cls._instance is None:
			cls._instance = cls()
		return cls._instance

	@property
	def dataaccess(self):
		return self._dataaccess

	@dataaccess.setter
	def dataaccess(self, value):
		self._dataaccess = value

	def add_class_mapper(self, tablename):
		su_clas = type(tablename, (SpatialUnitRepository,), {})
		self._types[tablename] = su_clas
		metadata = MetaData()
		su_table = Table(tablename, metadata,
			Column('suid', Integer, primary_key=True),
			autoload=True, 
			autoload_with=self._dataaccess.engine
		)

		ri_tablename = f'{tablename}{self._risk_indicator_suffix}'
		ri_clas = type(ri_tablename, (RiskIndicator,), {})
		self._types[ri_tablename] = ri_clas
		ri_table = Table(ri_tablename, metadata,
			Column('id', Integer, primary_key=True, autoincrement=True),
			Column('percentage', Float),
			Column('area', Float),
			Column('classname', String),
			Column('date', Date),
			Column('suid', Integer, ForeignKey(f'{su_table}.suid'), nullable=False),
		)		

		mapper(su_clas, su_table, properties={
			'indicator': relationship(ri_clas, backref='su', uselist=False)
		})	
		mapper(ri_clas, ri_table)	
		metadata.create_all(bind=self._dataaccess.engine)	

	def create_spatial_unit(self, tablename: str, as_attribute_name: str) -> SpatialUnitRepository:
		return self._types[tablename](tablename, as_attribute_name, self.dataaccess)	

	def create_risk_indicator(self, spatial_unit_tablename: str) -> RiskIndicator:
		tablename = f'{spatial_unit_tablename}{self._risk_indicator_suffix}'
		return self._types[tablename]()

	def risk_indicator_class(self, spatial_unit_tablename: str):
		tablename = f'{spatial_unit_tablename}{self._risk_indicator_suffix}'
		return self._types[tablename]	

	def spatial_unit_class(self, tablename: str):
		return self._types[tablename]	
