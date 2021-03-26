from sqlalchemy import (MetaData, Table, Column, ForeignKey, 
						Integer, String)
from ams.dataaccess import Base


class RiskIndicator:
	"""RiskIndictor"""
	"""Mapped in SpatialUnitDynamicFactory"""
	pass


class SpatialUnits(Base):
	"""SpatialUnitsRepository"""
	__tablename__ = 'spatial_units'
	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False, unique=True)
	as_attribute_name = Column(String, nullable=False)
		