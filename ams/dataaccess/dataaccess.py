from abc import ABC, abstractmethod


class DataAccess:
	@abstractmethod
	def connect(self, url: str):
		pass