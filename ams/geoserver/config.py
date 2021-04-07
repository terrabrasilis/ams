class Config:
	"""Config"""
	def __init__(self):
		self._workspace = 'ams'

	@property
	def workspace(self):
		return self._workspace
	
		