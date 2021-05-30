import pyproj
import shapely.ops as ops
from functools import partial
from shapely.geometry.base import BaseGeometry
from ams.domain.entities import Geometry


class ShapelyGeometry(Geometry):
	"""ShapelyGeometry"""
	
	def __init__(self, geom: BaseGeometry):
		self._geom = geom

	@property
	def area(self):
		return self._geom.area

	# @property
	# def bounds(self):
	# 	return self._geom.bounds

	def intersects(self, other: Geometry) -> bool:
		return self._geom.intersects(other._geom)

	def intersection(self, other: Geometry) -> Geometry:
		return ShapelyGeometry(self._geom.intersection(other._geom))

	def transform(self):
		proj = partial(pyproj.transform, 
				pyproj.Proj(init='epsg:4326'),
               	pyproj.Proj(init='epsg:5880'))
		return ops.transform(proj, self._geom)

# s_new = transform(proj, s)
# 		return ops.transform(
# 			partial(
# 				pyproj.transform,
# 				pyproj.Proj(init='EPSG:4326'),
# 				pyproj.Proj(
# 					proj='aea',
# 					lat_1=self._geom.bounds[1],
# 					lat_2=self._geom.bounds[3])),
# 				self._geom)		
