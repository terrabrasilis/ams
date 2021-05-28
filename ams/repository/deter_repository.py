import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.automap import automap_base
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, Date
from geoalchemy2.shape import to_shape
from ams.gis import ShapelyGeometry
from ams.domain.entities import DeterAlert, DeterAlerts


url = os.environ.get('DETER_DATABASE_URL') or\
	'postgresql://postgres:postgres@localhost:5432/DETER-B'
Base = automap_base()
engine = create_engine(url)
Session = scoped_session(sessionmaker(bind=engine))   


# https://stackoverflow.com/a/28727066/3050042
class DeterRepositoryMeta(type(Base), type(DeterAlerts)):
	pass


class DeterRepository(Base, DeterAlerts, metaclass=DeterRepositoryMeta):
	__tablename__ = 'deter_table'
	__table_args__ = {'schema': 'terrabrasilis'}

	gid = Column(Integer, primary_key=True)
	classname = Column(String, nullable=False)
	date = Column(Date, nullable=False)
	geom = Column(Geometry('GEOMETRY', srid=4326), nullable=False)

	@property
	def id(self):
		return self._gid

	def get(self, id: int) -> DeterAlert:
		session = Session()
		alert = session.query(self.__class__).get(id)
		session.close()
		return self._to_deter_alert(alert)

	def list(self, start: datetime.date = None, 
				end: datetime.date = None, 
				limit: int = None) -> 'list[DeterAlert]':
		session = Session()
		alerts = None
		if start and end:
			alerts = session.query(self.__class__)\
						.filter(self.__class__.date >= end)\
						.filter(self.__class__.date <= start)\
						.order_by(self.__class__.date.desc())
		else:
			alerts = session.query(self.__class__).order_by(
				self.__class__.date.desc()).limit(limit).all()
		session.close()
		return [self._to_deter_alert(alert) for alert in alerts]

	def _to_deter_alert(self, alert):
		geom = ShapelyGeometry(to_shape(alert.geom))
		return DeterAlert(alert.gid, alert.classname, alert.date, geom)


class DeterHistoricalRepository(DeterRepository):
	__tablename__ = 'deter_history'

	gid = Column(Integer, primary_key=True)
	classname = Column(String, nullable=False)
	date = Column(Date, nullable=False)
	geom = Column(Geometry('GEOMETRY', srid=4326), nullable=False)

	__mapper_args__ = {
		'concrete': True
	}	


Base.prepare(engine, reflect=True)
