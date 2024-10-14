from psycopg2 import connect

import json


class AppConfigController:
    """AppConfigController"""

    def __init__(self, db_url: str):
        self._conn = connect(db_url)

    def read_class_groups(self, biomes):
        """
        Gets the class names grouped by class groups.
        Including class titles and a required order to use on the frontend
        to display filters by classes.
        """
        sql = """SELECT string_agg( c1 || ',' || c2, ', ' )
		FROM (
			SELECT '{''name'':'''||dcg.name||''', ''title'':'''||dcg.title||'''' as c1,
			dcg.orderby, '''classes'':[' || string_agg(''''||dc.name||'''', ',') || ']}' as c2
			FROM public.class_group dcg, public.class dc
			WHERE dcg.id=dc.group_id AND dc.biome IN (%s)
                        GROUP BY 1,2 ORDER BY dcg.orderby
		) as tb1"""
        cur = self._conn.cursor()
        cur.execute(sql % ",".join([f"'{_}'" for _ in biomes]))
        results = cur.fetchall()
        return "["+results[0][0]+"]"

    def read_land_uses(self):
        """
        Gets the land use ids and names.
        To use on the frontend to display filters by land uses.
        """
        sql = """SELECT string_agg( lu , ', ' )
		FROM (
			SELECT '{''id'':'||id||', ''name'':'''||name||'''}' as lu
			FROM public.land_use ORDER BY priority
		) as tb1"""
        cur = self._conn.cursor()
        cur.execute(sql)
        results = cur.fetchall()
        return "["+results[0][0]+"]"

    def read_spatial_units_for_subset(self, subset, biome="ALL"):
        """
        Gets the spatial units from database for the given subset.
        """
        sql = """
        WITH date_agg AS (
            SELECT su.id as spatial_unit_id, su.dataname, su.description, su.center_lat, su.center_lng, MAX(pd.date) AS last_date
            FROM public.spatial_units su, deter.deter_publish_date pd
            WHERE su.id IN (
                SELECT spatial_unit_id
                FROM public.spatial_units_subsets
                WHERE subset = '%s'
            )
            AND ('%s' = 'ALL' OR pd.biome = '%s')
            GROUP BY su.id
            ORDER BY su.id ASC
        )
        SELECT string_agg(
            '{''dataname'':''' || da.dataname ||
            ''',''description'':''' || da.description ||
            ''',''center_lat'':''' || da.center_lat || 
            ''',''center_lng'':''' || da.center_lng ||
            ''',''last_date'':''' || da.last_date ||
            '''}', 
            ','
        ) AS c1
        FROM date_agg da;
        """
        sql = sql % (subset, biome, biome)
        cur = self._conn.cursor()
        cur.execute(sql)
        results = cur.fetchall()
        return "["+results[0][0]+"]"

    def read_biomes(self):
        """
        Gets the biomes from database.
        """
        sql = "SELECT biome from public.biome"
        cur = self._conn.cursor()
        cur.execute(sql)
        results = [_[0] for _ in cur.fetchall()]
        return json.dumps(results)

    def read_municipalities(self):
        """
        Gets the municipalities from database.
        """
        sql = "SELECT name from public.municipalities_group"
        cur = self._conn.cursor()
        cur.execute(sql)
        results = [_[0] for _ in cur.fetchall()]
        return json.dumps(results)

    def read_municipality_biomes(self, municipality=None):
        """
        Gets the biomes from database.
        """
        sql = f"""
           SELECT DISTINCT mb.biome
           FROM public.municipalities_biome mb
           WHERE geocode IN (
              SELECT geocode
              FROM public.municipalities_group_members mgm
              WHERE mgm.group_id = (
                 SELECT mg.id
                 FROM public.municipalities_group mg
                 WHERE mg.name='{municipality}'
              )
           )
        """
        cur = self._conn.cursor()
        cur.execute(sql)
        results = [_[0] for _ in cur.fetchall()]
        return json.dumps(results)
