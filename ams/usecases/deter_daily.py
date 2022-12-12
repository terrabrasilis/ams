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

    def __init__(self, db_url: str, biome: str, alldata=False):
        self._conn = connect(db_url)
        self._alldata = alldata
        self._biome = biome
        # ignore classes that are not related to DETER data.
        # For more than one, use single quotes and comma like this: "'AF','DS','EX'"
        self.ignore_classes="'AF'" # AF=Active Fires by now.
        print('Processing the DETER alerts data...')

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

        tables={'deter','deter_auth'}
        if(self._alldata):
            tables={'deter','deter_auth','deter_history'}

        # update current data from local deter tables
        for table in tables:
            truncate=f"""TRUNCATE deter.{table};"""
            insert=f"""
            INSERT INTO deter.{table}(
                gid, origin_gid, classname, quadrant, orbitpoint, date, sensor, satellite,
                areatotalkm, areamunkm, areauckm, mun, uf, uc, geom, month_year, ncar_ids, car_imovel, continuo,
                velocidade, deltad, est_fund, dominio, tp_dominio
            )
            SELECT deter.gid, deter.origin_gid, deter.classname, deter.quadrant, deter.orbitpoint, deter.date,
            deter.sensor, deter.satellite, deter.areatotalkm,
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
            if(self._biome=="'Amazônia'"):
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

    def create_publish_date_table(self):
        """
        Create a publish date table from DETER publish date original data.
        *Required to improve SQL runtime because this table is used in GeoServer SQL VIEW layer.

        Prerequisites (see database requirements section in README.md):
         - Existence of "public.deter_publish_date" SQL VIEW in the database;
         - Existence of "deter" Schema in database;
        """
        # drop the deter.deter_publish_date table if exists
        drop="""DROP TABLE IF EXISTS deter.deter_publish_date;"""
        
        # recreate deter.deter_publish_date
        create="""
        CREATE TABLE IF NOT EXISTS deter.deter_publish_date AS
        SELECT date FROM public.deter_publish_date
        """
        cur = self._conn.cursor()
        cur.execute(drop)
        cur.execute(create)
        print('The deter.deter_publish_date table has been created.')

    def update_data(self):
        """
        Read DETER data from official databases using some SQL views
        that were created in the database earlier.
        
        See the README.md file in the "Database requirements" section for details on prerequisites
        """
        # update the current DETER data table
        self.update_current_tables()
        # recreate the publish date table
        self.create_publish_date_table()
        # create the DETER temporary data table
        self.create_tmp_table()

    def execute(self):
        try:
            print("Starting at: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
            self.update_data()
            print("Finished in: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print('Error executing DETER data update')
            print(e.__str__())
            raise e

# local test
# db='postgresql://postgres:postgres@192.168.15.49:5444/AMST'
# dd = DeterDaily(db_url=db, alldata=False)
# dd.execute()