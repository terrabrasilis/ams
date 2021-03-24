from abc import ABC, abstractmethod
import datetime
from .deter_alert import DeterAlert


class DeterAlerts(ABC):
	"""DeterAlerts"""

	@abstractmethod
	def get(self, id: int) -> DeterAlert:
		pass

	@abstractmethod
	def list(self, start: datetime.date, end: datetime.date) -> 'list[DeterAlert]':
		pass
		