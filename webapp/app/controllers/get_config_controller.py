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
			SELECT '{''name'':'''||cg.name||''', ''title'':'''||cg.title||'''' as c1,
			cg.orderby, '''classes'':[' || string_agg(''''||c.name||'''', ',') || ']}' as c2
			FROM public.class_group cg
                        JOIN public.class c
                        ON cg.id=c.group_id
                        WHERE (%s = 'ALL' OR c.biome IN (%s))
                        GROUP BY 1,2 ORDER BY cg.orderby
		) as tb1"""
        biomes = ",".join([f"'{_}'" for _ in biomes])
        sql = sql % (biomes, biomes)
        cur = self._conn.cursor()
        cur.execute(sql)
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

    def read_spatial_units_for_subset(self, subset, biome="ALL", exclude=[]):
        """
        Gets the spatial units from database for the given subset.
        """
        exclude_filter = ""
        if exclude:
            cols = ",".join([f"'{_}'" for _ in exclude])
            exclude_filter = f"AND su.dataname NOT IN ({cols})"  

        sql = """
        WITH date_agg AS (
            SELECT su.id as spatial_unit_id, su.dataname, su.description, su.center_lat, su.center_lng, MAX(pd.date) AS last_date
            FROM public.spatial_units su, deter.deter_publish_date pd
            WHERE su.id IN (
                SELECT spatial_unit_id
                FROM public.spatial_units_subsets
                WHERE subset = '%s'
            )
            %s
            AND ('%s' = 'ALL' OR pd.biome = '%s')
            GROUP BY su.id
            ORDER BY su.dataname ASC
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
        sql = sql % (subset, exclude_filter, biome, biome)

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

    def read_municipalities_group(self):
        """
        Gets the municipalities group from database.
        """
        sql = "SELECT name from public.municipalities_group"
        cur = self._conn.cursor()
        cur.execute(sql)
        results = ["customizado"] + [_[0] for _ in cur.fetchall()]
        return json.dumps(results)

    def read_publish_date(self, biomes):
        """
        Gets the deter publish date.
        """
        biomes  = ",".join([f"'{_}'" for _ in biomes])

        sql = f"""
            SELECT MAX(date) FROM deter.deter_publish_date dpd
            WHERE ('ALL' IN (%s) OR dpd.biome IN (%s));
        """
        
        cur = self._conn.cursor()
        cur.execute(sql % (biomes, biomes))
        return cur.fetchone()[0].strftime("%Y-%m-%d")

    def read_municipalities(self, biomes):
        """
        Gets the municipalities from database.
        """
        sql = """
            WITH municipalities_agg AS (
                SELECT DISTINCT REPLACE(CONCAT(mun.name, ' - ', mun.state_acr, ' - geoc\xf3digo: ', mun.geocode), '''', ' ') as name, mun.geocode
	        FROM public.municipalities mun, public.municipalities_biome mub
	        WHERE
                    mun.geocode = mub.geocode
		    AND mub.biome = ANY('{%s}')
	        ORDER BY name
            )
            SELECT string_agg(
	        '{''name'':''' || ma.name ||
                ''',''geocode'':''' || ma.geocode ||
                '''}',
	        ','
           )
           FROM municipalities_agg ma;
        """
        sql = sql % (",".join([f"{_}" for _ in biomes]))
        cur = self._conn.cursor()
        cur.execute(sql)
        results = cur.fetchall()
        return "["+results[0][0]+"]"

    def read_municipality_name(self, geocode):
        """
        Gets the municipalities from database.
        """
        sql = f"""
            SELECT DISTINCT REPLACE(CONCAT(mun.name, ' - ', mun.state_acr), '''', ' ') as name, mun.geocode
	    FROM public.municipalities mun
	    WHERE mun.geocode = '{geocode}';
        """
        cur = self._conn.cursor()
        cur.execute(sql)
        results = cur.fetchone()

        if len(results):
            return results[0]

        return None

    def read_municipality_geocode(self, su_id):
        """
        Gets the municipality geocode from database.
        """
        sql = f"""
           SELECT mun.geocode FROM public.municipalities mun
           WHERE mun.suid='{su_id}'
        """
        cur = self._conn.cursor()
        cur.execute(sql)
        results = cur.fetchone()

        if results:
            return results[0]

        return None

    def read_bbox(self, subset, biome, municipalities_group, geocodes):
        """
        Gets the layer bounding box.
        """
        sql = ""
        if subset == "Bioma":
            sql = f"""
                SELECT
                    ST_XMin(ST_Extent(geom)) AS xmin,
                    ST_XMax(ST_Extent(geom)) AS xmax,
                    ST_YMin(ST_Extent(geom)) AS ymin,
                    ST_YMax(ST_Extent(geom)) AS ymax
                FROM public.biome_border
                WHERE biome='{biome}';
            """
        else:
            sql = f"""
                SELECT
                    ST_XMin(ST_Extent(mun.geometry)) AS xmin,
                    ST_XMax(ST_Extent(mun.geometry)) AS xmax,
                    ST_YMin(ST_Extent(mun.geometry)) AS ymin,
                    ST_YMax(ST_Extent(mun.geometry)) AS ymax
                FROM public.municipalities mun
                WHERE mun.geocode = ANY(
                    SELECT geocode
                    FROM public.municipalities_group_members mgm
                    WHERE mgm.group_id = (
                        SELECT mg.id
                        FROM public.municipalities_group mg
                        WHERE mg.name='{municipalities_group}'
                    )
                ) OR mun.geocode = ANY('{{{geocodes}}}');
            """

        cur = self._conn.cursor()
        cur.execute(sql)
        results = cur.fetchone()

        return json.dumps(results)

    def geocode_is_valid(self, geocode):
        """
        Check if the geocode is valid.
        """
        sql = f"""
           SELECT mun.geocode FROM public.municipalities mun
           WHERE mun.geocode='{geocode}'
        """
        cur = self._conn.cursor()
        cur.execute(sql)
        results = cur.fetchone()

        return results is not None
