from shapely.geometry.base import BaseGeometry
from ams.entities import Geometry


class ShapelyGeometry(Geometry):
	"""ShapelyGeometry"""
	
	def __init__(self, geom: BaseGeometry):
		self._geom = geom

	@property
	def area(self):
		return self._geom.area

	def intersects(self, other: Geometry) -> bool:
		return self._geom.intersects(other._geom)

	def intersection(self, other: Geometry) -> Geometry:
		return ShapelyGeometry(self._geom.intersection(other._geom))	
