from datetime import datetime
from psycopg2 import connect

class ActiveFires:
    """
    ActiveFires class

    Used to:
     - Copy points of active fires from a external database to complete the local database table;
     - Counting the number of points intercept with the spatial units;

    @param {str} db_url, the PostgreSQL database connection parameters as string format.
    Example: "postgresql://<user>:<password>@<host or ip>:<port>/<database_name>"

    @param {str} biome, the name of biome used to filter active fires data.
    See the names in raw_active_fires table. Ex.: "Amazônia"

    @param {boolean} alldata, Default is False, if True, all data of RAW database will be processed.
    Otherwise, only new data is processed.    
    """

    def __init__(self, db_url: str, biome: str, alldata=False):
        self._conn = connect(db_url)
        self._alldata = alldata
        self._fires_input_table = 'fires.active_fires'
        self._biome = biome 
        print(f'Processing the Active Fires data...')

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

    def update_focuses_table(self):
        print(f'Insert fires data from raw database via SQL View ...')
        """
        Load active fire data from raw database using a SQL View resource named public.raw_active_fires
        *raw database has an independent sync task.
        """
        
        bydate = " AND a.view_date > '2016-01-01'::date "
        cur = self._conn.cursor()

        if(self._alldata):
            cur.execute(f"TRUNCATE {self._fires_input_table};")
        else:
            bydate = f" AND a.view_date > ( SELECT MAX(view_date) FROM {self._fires_input_table} )"

        update = f"""
        INSERT INTO {self._fires_input_table}(id, uuid, view_date, satelite, estado, municipio, geom)
        SELECT a.id, a.uuid, a.view_date, a.satelite, a.estado, a.municipio, a.geom
        FROM public.raw_active_fires a
        WHERE a.bioma = '{self._biome}'
        {bydate}
        """
        cur.execute(update)

    def execute(self):
        try:
            print("Starting at: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
            self.read_spatial_units()
            self.update_focuses_table()
            print("Finished in: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print('Error on statistics generation for Active Fires')
            print(e.__str__())
            raise e

# local test
# db='postgresql://postgres:postgres@192.168.15.49:5444/AMST'
# ac = ActiveFires(db_url=db)
# ac.execute()