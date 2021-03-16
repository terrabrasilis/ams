from sqlalchemy import (MetaData, Table, Column, ForeignKey, 
						Integer, String)
from sqlalchemy.orm import mapper
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session


class SpatialUnitRepository():
	"""docstring for SpatialUnitRepository"""

	def __init__(self, tablename, engine):
		metadata = MetaData()
		metadata.reflect(engine)
		table = metadata.tables.get(tablename)
		if table is not None:
			metadata.remove(table)
		table = Table(tablename, metadata,
			Column('fid', Integer, primary_key=True),
			Column('id', String)
		)		
		mapper(self.__class__, table)
		self._engine = engine

	def list(self):
		Session = scoped_session(sessionmaker(bind=self._engine))  
		session = Session()
		all_data = session.query(self.__class__).all()
		session.close()
		return [self._to_dict(d) for d in all_data]	

	def _to_dict(self, dat):
		return {
			'fid': dat.fid,
			'id': dat.id
		}	

