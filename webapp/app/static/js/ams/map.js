from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database, drop_database
from .dataaccess import DataAccess


Base = declarative_base()


class AlchemyDataAccess(DataAccess):
	def connect(self, url: str):
		self._engine = create_engine(url)
		self._session = scoped_session(sessionmaker(bind=self._engine))   
		self._url = url   

	def create_session(self):
		return SessionProxy(self._session)

	@property
	def engine(self):
		return self._engine

	def create(self, overwrite: bool = False):
		if database_exists(self._url):
			if overwrite:
				drop_database(self._url)
				create_database(self._url)
		else:
			create_database(self._url)

	def add_postgis_extension(self):
		conn = self._engine.connect()
		conn.execute('commit')
		try:
			conn.execute('CREATE EXTENSION postgis')
		except Exception as e:
			raise e
		conn.close()

	def exists(self):
		return database_exists(self._url)

	def drop(self):
		drop_database(self._url)	

	def create_all_tables(self):
		Base.metadata.create_all(self._engine)

	def create_all(self, overwrite: bool = False):
		self.create(overwrite)
		self.create_all_tables()			


class SessionProxy():
	def __init__(self, session):
		self._session = session

	def commit(self):
		try:
			self._session.commit()
		except exc.IntegrityError as e:
			self._session.rollback()
			self._session.close()
			if 'NotNullViolation' in str(e):
				raise NotNullViolationExceptionError('Object violates not-null constraint.')
			else:
				raise e

	def add(self, object):
		self._session.add(object)

	def delete(self, object):
		self._session.delete(object)

	def expunge(self, object):
		self._session.expunge(object)

	def close(self):
		self._session.close()

	def query(self, object):
		return self._session.query(object)


class NotNullViolationExceptionError(Exception):
	pass
