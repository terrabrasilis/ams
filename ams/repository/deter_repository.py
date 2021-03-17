from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.automap import automap_base
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, Date
from geoalchemy2.shape import to_shape


url = 'postgresql://postgres:postgres@localhost:5432/DETER-B'
Base = automap_base()
engine = create_engine(url)
Session = scoped_session(sessionmaker(bind=engine))   


class DeterRepository(Base):
	__tablename__ = 'deter_table'
	__table_args__ = {'schema': 'terrabrasilis'}

	gid = Column(Integer, primary_key=True)
	classname = Column(String)
	date = Column(Date)
	publish_month = Column(Date)
	geom = Column(Geometry('POLYGON', srid=5880))

	def get(self, id):
		session = Session()
		res = session.query(self.__class__).get(id)
		session.close()
		return self._to_dict(res)

	def list(self):
		session = Session()
		all_alerts = session.query(self.__class__).all()
		session.close()
		return [self._to_dict(alert) for alert in all_alerts]

	def _to_dict(self, alert):
		return {
			'gid': alert.gid,
			'classname': alert.classname,
			'date': alert.date,
			'geom': to_shape(alert.geom)
		}

Base.prepare(engine, reflect=True)
