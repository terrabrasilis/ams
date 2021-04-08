from sqlalchemy import Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship
from ams.dataaccess import Base


class RiskIndicator:
	"""RiskIndictor"""
	"""Mapped in SpatialUnitDynamicFactory"""
	pass


class SpatialUnitInfo(Base):
	"""SpatialUnitInfo"""
	__tablename__ = 'spatial_units'
	id = Column(Integer, primary_key=True)
	dataname = Column(String, nullable=False, unique=True)
	as_attribute_name = Column(String, nullable=False)
	center_lat = Column(Float, nullable=False)
	center_lng = Column(Float, nullable=False)


class DeterClassGroup(Base):
	"""DeterClassGroup"""
	__tablename__ = 'deter_class_group'
	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False, unique=True)
	classes = relationship('DeterClass', back_populates='group')


class DeterClass(Base):
	"""DeterClass"""
	__tablename__ = 'deter_class'
	id = Column(Integer, primary_key=True)
	name = Column(String, nullable=False, unique=True)
	group_id = Column(Integer, ForeignKey('deter_class_group.id'))
	group = relationship('DeterClassGroup', back_populates='classes')
