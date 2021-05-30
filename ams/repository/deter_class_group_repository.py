from ams.dataaccess import DataAccess
from ams import entities
from .alchemy_orm import DeterClassGroup, DeterClass


class DeterClassGroupRepository:
	"""DeterClassGroupRepository"""
	def __init__(self, dataaccess: DataAccess):
		self._dataaccess = dataaccess

	def list(self):
		session = self._dataaccess.create_session()
		groups = session.query(DeterClassGroup).all()
		result = [self._to_deter_group(g) for g in groups]
		session.close()
		return result

	def add(self, group: DeterClassGroup):
		session = self._dataaccess.create_session()
		grp = DeterClassGroup()
		grp.name = group.name
		for cname in group.classes:
			clas = DeterClass()
			clas.name = cname
			grp.classes.append(clas)
		session.add(grp)
		session.commit()
		session.close()		

	def _to_deter_group(self, group):
		grp = entities.DeterClassGroup(group.name)
		for c in group.classes:
			grp.add_class(c.name)
		return grp
