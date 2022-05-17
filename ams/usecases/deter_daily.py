from datetime import datetime
from psycopg2 import connect

class DeterDaily:
    """
    DeterDaily class

    Used to:
     - Copy alerts from a external database to the local database table;
     - Compute the area for alerts that intercepts with the spatial units;

    DETER alerts have both historical and current data.
    For current data, this script deletes all data from the local table and copies it back from
    the production database, so related statistics are calculated every day.

    For historical data, we assume the data table is static and already exists in the database
    as an SQL View pointing to the source database.
    Otherwise, you must provide this SQL View before running historical statistics.
    See the README.md file for instructions.

    @param {boolean} alldata, Default is False, if True, all data of DETER will be processed, historical and current.
    Otherwise, only current is processed.

    """

    def __init__(self, db_url: str, alldata=False):
        self._conn = connect(db_url)
        self._alldata = alldata
        # ignore classes that are not related to DETER data.
        # For more than one, use single quotes and comma like this: "'AF','DS','EX'"
        self.ignore_classes="'AF'" # AF=Active Fires by now.
        print('Processing the DETER alerts data...')

    def read_spatial_units(self):
        """
        Gets the spatial units from database.
        Prerequisites:
         - The public.spatial_units table must exist in the database and have data.
        See the README.md file for instructions.
        """
        self._spatial_units = {}
        sql = "SELECT dataname, as_attribute_name FROM public.spatial_units"
        cur = self._conn.cursor()
        cur.execute(sql)
        results=cur.fetchall()
        self._spatial_units=dict(results)

    def read_deter_classes(self):
        """
        Gets the alert classes from database.
        Prerequisites:
         - The public.deter_class and public.deter_class_group tables must exist in the database and have data.
        See the README.md file for instructions.
        """
        self._deter_classes = {}
        sql = f"""SELECT d.name as classname, dg.name as classgroup
        FROM public.deter_class as d, public.deter_class_group as dg
        WHERE d.group_id=dg.id AND dg.name NOT IN ({self.ignore_classes})"""
        cur = self._conn.cursor()
        cur.execute(sql)
        results=cur.fetchall()
        self._deter_classes=dict(results)

    def update_current_tables(self):
        """
        Used to truncate data from current DETER tables and reinsert it.

        Prerequisites (see database requirements section in README.md):
         - Existence of SQL Views in the database;
         - Existence of "deter" Schema and tables in database;

        Load alerts data from raw database using a SQL View resource named public.deter and public.deter_auth
        *raw database has an independent sync task.
        """
        print('Insert DETER data from raw database via SQL View ...')
        cur = self._conn.cursor()
        # update current data from local deter tables
        for table in {'deter','deter_auth'}:
            truncate=f"""TRUNCATE deter.{table};"""
            insert=f"""
            INSERT INTO deter.{table}(
                gid, origin_gid, classname, quadrant, orbitpoint, date, date_audit, lot, sensor, satellite,
                areatotalkm, areamunkm, areauckm, mun, uf, uc, geom, month_year, ncar_ids, car_imovel, continuo,
                velocidade, deltad, est_fund, dominio, tp_dominio
            )
            SELECT deter.gid, deter.origin_gid, deter.classname, deter.quadrant, deter.orbitpoint, deter.date,
            deter.date_audit, deter.lot, deter.sensor, deter.satellite, deter.areatotalkm,
            deter.areamunkm, deter.areauckm, deter.mun, deter.uf, deter.uc, deter.geom, deter.month_year,
            0::integer as ncar_ids, ''::text as car_imovel,
            0::integer as continuo, 0::numeric as velocidade,
            0::integer as deltad, ''::character varying(254) as est_fund,
            ''::character varying(254) as dominio, ''::character varying(254) as tp_dominio
            FROM public.{table} as deter;
            """
            update=f"""
            UPDATE deter.{table}
            SET ncar_ids=ibama.ncar_ids, car_imovel=ibama.car_imovel, velocidade=ibama.velocidade,
            deltad=ibama.deltad, est_fund=ibama.est_fund, dominio=ibama.dominio, tp_dominio=ibama.tp_dominio
            FROM public.deter_aggregated_ibama as ibama
            WHERE deter.{table}.origin_gid=ibama.origin_gid
            AND deter.{table}.areamunkm=ibama.areamunkm
            AND (ibama.ncar_ids IS NOT NULL OR ibama.est_fund IS NOT NULL OR ibama.dominio IS NOT NULL);
            """
            cur.execute(truncate)
            cur.execute(insert)
            cur.execute(update)
            print(f'DETER alerts for {table} have been updated.')

    def drop_tmp_table(self):

        drop="""DROP TABLE IF EXISTS deter.tmp_data"""
        cur = self._conn.cursor()
        cur.execute(drop)
        print(f'The deter temp table has been removed.')

    def create_tmp_table(self):
        """
        Create a temporary data table with DETER alerts to ensure gist index creation.

        Prerequisites (see database requirements section in README.md):
         - Existence of "deter.deter_history" table in the database (if alldata is True);
         - Existence of "deter" Schema in database;
         - Existence of table "deter.deter_auth" filled in the database (call the update_current_tables before that function);
        """
        # drop the DETER temporary data table if exists
        self.drop_tmp_table()

        union=""
        if(self._alldata):
            union="""
            UNION
            SELECT gid||'_h' as gid, classname, date, areamunkm, geom
            FROM deter.deter_history
            """
        create=f"""
        CREATE TABLE IF NOT EXISTS deter.tmp_data AS
        SELECT tb.gid, tb.classname, tb.date, tb.areamunkm, tb.geom
        FROM (
            SELECT gid, classname, date, areamunkm, geom
            FROM deter.deter_auth
            {union}
        ) as tb
        """
        index="""
        CREATE INDEX IF NOT EXISTS index_deter_tmp_table_geom
        ON deter.tmp_data USING gist
        (geom)
        """
        cur = self._conn.cursor()
        cur.execute(create)
        cur.execute(index)
        print('The DETER temp table has been created.')

    def statistics_processing(self):
        """
        Processing of statistics for DETER alerts crossing with tables of spatial units
        registered in the metadata model.
        The metadata model is composed of three tables, "spatial_units", "deter_class" and
        "deter_class_group" where spatial units and DETER classes are registered, so it is expected
        that the information represents the names and current classes of the tables.
        See the README.md file for instructions.
        """
        # create spatial unit tables if not exists
        self.create_spatial_risk_tables()
        # update the current DETER data table
        self.update_current_tables()
        # create the DETER temporary data table
        self.create_tmp_table()
        
        cur = self._conn.cursor()
        for spatial_unit, id in self._spatial_units.items():
            
            # remove all stats from a spatial unit, but ignore some classes from the ignore list.
            delete=f"""
            DELETE FROM public."{spatial_unit}_risk_indicators"
            WHERE classname NOT IN ({self.ignore_classes})
            """
            if(not self._alldata):
                # remove statistics only for current DETER data
                delete=f"""{delete} AND date>=(SELECT MIN(date) FROM deter.deter_auth)"""

            cur.execute(delete)
            print(f'The {spatial_unit} statistics has been deleted.')

            # for each classname, processing the statistics
            for classname, classgroup in self._deter_classes.items():
                
                insert=f"""
                WITH results AS (
                    SELECT dt.date as date, su.suid, SUM(dt.areamunkm) as area,
                    SUM(dt.areamunkm*100/(ST_Area(su.geometry::geography)/1000000)) as percentage
                    FROM deter.tmp_data dt, public."{spatial_unit}" su
                    WHERE dt.classname='{classname}'
                    AND (su.geometry && dt.geom) AND ST_Intersects(dt.geom, su.geometry) 
                    GROUP BY 1,2
                )
                INSERT INTO public."{spatial_unit}_risk_indicators"(classname, date, suid, area, percentage)
                SELECT '{classgroup}' as classname, a.date, a.suid, a.area, a.percentage
                FROM results a
                """
                cur.execute(insert)
                print(f'The {classname} statistic has been updated.')

    def create_spatial_risk_tables(self):
        """
        Use this function to create "<spatial_unit>_risk_indicators" tables.
        If these tables already exist they will not be created.
        """
        cur = self._conn.cursor()
        for spatial_unit, id in self._spatial_units.items():
            create=f"""
            CREATE TABLE IF NOT EXISTS public."{spatial_unit}_risk_indicators"
            (
                id serial NOT NULL,
                percentage double precision,
                area double precision,
                classname character varying(2),
                date date,
                suid integer NOT NULL,
                counts integer,
                CONSTRAINT "{spatial_unit}_risk_indicators_pkey" PRIMARY KEY (id),
                CONSTRAINT "{spatial_unit}_risk_indicators_suid_fkey" FOREIGN KEY (suid)
                    REFERENCES public."{spatial_unit}" (suid) MATCH SIMPLE
                    ON UPDATE NO ACTION
                    ON DELETE NO ACTION
            )
            TABLESPACE pg_default
            """
            cur.execute(create)
            print(f'The {spatial_unit}_risk_indicators table has been created.')

    def execute(self):
        try:
            print("Starting at: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
            self.read_spatial_units()
            self.read_deter_classes()
            self.statistics_processing()
            print("Finished in: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print('Error on statistics generation for Active Fires')
            print(e.__str__())
            raise e

# local test
# db='postgresql://postgres:postgres@192.168.15.49:5444/AMST'
# dd = DeterDaily(db_url=db, alldata=False)
# dd.execute()