from abc import ABC, abstractmethod


class DataAccess(ABC):
	@abstractmethod
	def connect(self, url: str):
		pass
