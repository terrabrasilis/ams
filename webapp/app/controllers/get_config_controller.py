from psycopg2 import connect

class AppConfigController:
	"""AppConfigController"""
	
	def __init__(self, db_url: str):
		self._conn = connect(db_url)

	def read_spatial_units(self):
		"""
		Gets the spatial units from database.
		Prerequisites:
			- The public.spatial_units table must exist in the database and have data.
		See the README.md file for instructions.
		"""
		sql = """SELECT string_agg('{''dataname'':'''||su.dataname||
		''',''center_lat'':'|| su.center_lat || 
		',''center_lng'':'|| su.center_lng ||
		',''last_date'':'''||pd.date||'''}', ',') 
		FROM public.spatial_units su, deter.deter_publish_date pd"""
		cur = self._conn.cursor()
		cur.execute(sql)
		results=cur.fetchall()
		return "["+results[0][0]+"]"

	def read_class_groups(self):
		"""
		Gets the most recent date for each spatial unit data.
		Prerequisites:
			- The self._spatial_units data must to have readed before.
		"""
		sql = """SELECT string_agg( c1 || ',' || c2, ', ' )
		FROM (
			SELECT '{''name'':'''||dcg.name||'''' as c1, '''classes'':[' || string_agg(''''||dc.name||'''', ',') || ']}' as c2
			FROM public.deter_class_group dcg, public.deter_class dc
			WHERE dcg.id=dc.group_id GROUP BY 1
		) as tb1"""
		cur = self._conn.cursor()
		cur.execute(sql)
		results=cur.fetchall()
		return "["+results[0][0]+"]"
