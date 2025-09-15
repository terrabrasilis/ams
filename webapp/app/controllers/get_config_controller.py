from psycopg2 import connect
from datetime import datetime

import json


class AppConfigController:
    """AppConfigController"""

    def __init__(self, db_url: str):
        try:
            self._conn = connect(db_url)
        except Exception as e:
            print("connection error", e)
            self._conn = None

    def is_connected(self):
        return not self._conn is None

    def read_class_groups(self, biomes, inpe_risk=True):
        """
        Gets the class names grouped by class groups.
        Including class titles and a required order to use on the frontend
        to display filters by classes.
        """
        risk_classname_to_ignore = "('RK')" if inpe_risk else "('RI')"

        sql = """SELECT string_agg( c1 || ',' || c2, ', ' )
		FROM (
			SELECT '{''name'':'''||cg.name||''', ''title'':'''||cg.title||'''' as c1,
			cg.orderby, '''classes'':[' || string_agg(DISTINCT ''''||c.name||'''', ',') || ']}' as c2
			FROM public.class_group cg
                        JOIN public.class c
                        ON cg.id=c.group_id
                        WHERE ('%s' = 'ALL' OR c.biome = ANY('{%s}'))
                              AND cg.name NOT IN %s
                        GROUP BY 1,2 ORDER BY cg.orderby            
		) as tb1"""

        biomes = ",".join(biomes)
       
        sql = sql % (biomes, biomes, risk_classname_to_ignore)

        cur = self._conn.cursor()
        cur.execute(sql)
        results = cur.fetchall()
        return "["+results[0][0]+"]"

    def read_land_uses(self, land_use_type):
        """
        Gets the land use ids and names.
        To use on the frontend to display filters by land uses.
        """
        land_use_type_suffix = "" if land_use_type == "ams" else f"_{land_use_type}"

        sql = """SELECT string_agg( lu , ', ' )
		FROM (
			SELECT '{''id'':'||id||', ''name'':'''||name||'''}' as lu
			FROM public.land_use%s ORDER BY priority
		) as tb1"""
        sql = sql % land_use_type_suffix
        
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

        date = datetime.now().strftime("%Y-%m-%d")

        sql = """
        WITH date_agg AS (
            SELECT su.id as spatial_unit_id, su.dataname, su.description, su.center_lat, su.center_lng, '%s'::date AS last_date
            FROM public.spatial_units su, deter.deter_publish_date pd
            WHERE su.id IN (
                SELECT spatial_unit_id
                FROM public.spatial_units_subsets
                WHERE subset = '%s'
            )
            %s
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

        sql = sql % (date, subset, exclude_filter)

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

    def read_municipalities_group(self, gtype="user-defined", customized=True):
        """
        Gets the municipalities group from database.
        """
        sql = """
            SELECT name from public.municipalities_group
            WHERE type='%s'
            ORDER BY name ASC;
        """
        sql = sql % gtype
       
        cur = self._conn.cursor()
        cur.execute(sql)

        results = ["customizado"] if customized else []
        results =  results + [_[0] for _ in cur.fetchall()]

        return json.dumps(results)

    def read_municipalities_geocode(self, municipality_group):
        """
        Gets the municipalities geocode from database.
        """
        sql = """
            SELECT geocode
            FROM public.municipalities_group_members mgm
            INNER JOIN public.municipalities_group mg ON mg.id = mgm.group_id
            WHERE mg.name='%s';
        """
        sql = sql % municipality_group

        cur = self._conn.cursor()
        cur.execute(sql)
        results = [_[0] for _ in cur.fetchall()]
        return results

    def read_municipalities_biome(self, geocodes):
        """
        Gets the municipalities biome from database.
        """
        sql = """
            SELECT DISTINCT biome
            FROM public.municipalities_biome mb
            INNER JOIN public.municipalities mu ON mu.geocode=mb.geocode
            WHERE mu.geocode = ANY('{%s}');            
        """
        sql = sql % ','.join(geocodes)
        cur = self._conn.cursor()
        cur.execute(sql)
        results = [_[0] for _ in cur.fetchall()]
        return results

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

        return ""

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

        return ""

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

    def read_subsets(self):
        """
        Gets the subsets from database.
        """
        sql = "SELECT DISTINCT subset FROM public.spatial_units_subsets;"
        cur = self._conn.cursor()
        cur.execute(sql)
        results = [_[0] for _ in cur.fetchall()]

        return json.dumps(results)

    def read_classnames(self):
        """
        Gets the classnames from database.
        """
        sql = "SELECT name FROM public.class_group;"
        cur = self._conn.cursor()
        cur.execute(sql)
        results = [_[0] for _ in cur.fetchall()]

        return json.dumps(results)


    def read_spatial_units(self):
        """
        Gets the spatial units from database.
        """
        sql = "SELECT dataname FROM public.spatial_units;"
        cur = self._conn.cursor()
        cur.execute(sql)
        results = [_[0] for _ in cur.fetchall()]

        return json.dumps(results)
    

    def read_spatial_unit_names(self):
        """
        Gets the name of the spatial units from database.
        """
        spatial_units = json.loads(self.read_spatial_units())

        sqls = [
            f"SELECT name FROM public.{_}" for _ in spatial_units if not _.startswith("cs_")
        ]

        sql = " UNION ALL ".join(sqls) + ";"

        cur = self._conn.cursor()
        cur.execute(sql)
        results = [_[0] for _ in cur.fetchall()]

        return results


