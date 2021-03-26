from abc import ABC, abstractmethod


class Geometry(ABC):
	"""Geometry"""

	@property
	@abstractmethod
	def area(self) -> float:
		pass	
	
	@abstractmethod	
	def intersects(self, other: 'Geometry') -> bool:
		pass

	@abstractmethod
	def intersection(self, other: 'Geometry') -> 'Geometry':
		pass	
