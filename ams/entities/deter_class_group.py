class DeterClassGroup:
	"""DeterClassGroup"""
	def __init__(self, name: str):
		self._name = name
		self._classes = []

	@property
	def name(self) -> str:
		return self._name

	@property
	def classes(self) -> 'list[str]':
		return self._classes.copy()
	
	def add_class(self, classname: str):
		self._classes.append(classname)
