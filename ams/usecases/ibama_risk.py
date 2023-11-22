from os import path
from psycopg2 import OperationalError, connect
import geopandas as gpd
from sqlalchemy import create_engine
import rasterio as rio
from shapely.geometry import Point
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
from ams.dataaccess.ftp_ibama_risk import FtpIBAMARisk

class IBAMARisk:
    """
    Used to extract pixel values from the raster file provided by IBAMA and store these values in the PostGIS table in the database.

    The geotiff file represents the risk of deforestation in the matrix 1km X 1km in the Legal Amazon for one week.

    Prerequisites:
    -------------------------------------------------
     - The table in the database with the points as centroids of each pixel of the regular grid of the original matrix (1km X 1km)
     - The table in the database with the informations about the last downloaded file
    """

    def __init__(self, db_url:str, ftp:FtpIBAMARisk=None, srid:str="EPSG:4674", force_srid:bool=False, expiration_risk:int=7):
        """
        Settings for DB connection and file download.

        Mandatory parameters:
        -------------------------------------------------
        :param str db_url: The connection string to write data and log into database tables (See risk tables at scripts/startup.sql)
        :param FtpIBAMARisk ftp: The instance of FTP IBAMA Risk class used to download tiff file from FTP.
        
        Optional parameters:
        -------------------------------------------------
        :param str srid: The SRID code to apply to the entry data file on load to database. Default is EPSG:4674 (Geographic/SIRGAS2000)
        :param bool force_srid: Used to force the srid. Default is False.
        :param int expiration_risk: The number of days to set the risk forecast due date. Default is seven (7)
        """

        # FTP handler object
        self._ftp = ftp

        # database string connection
        self._db_url=db_url
        self._conn = None

        # risk model database entities
        self._db_schema = 'risk'
        self._risk_input_table = 'weekly_data'
        self._geom_table = 'matrix_ibama_1km'
        self._risk_expiration_table = 'risk_ibama_date'
        self._log_table = 'etl_log_ibama'
        self._risk_temp_table = 'weekly_ibama_tmp'

        # input data configuration
        self._SRID = srid if srid is not None else srid
        self._force_srid = force_srid

        # number of days to set the risk forecast due date
        self._ndays_of_expiration = expiration_risk

    def __get_db_cursor(self):
        """
        Gets the database cursor to run queries.
        
        Make a connection if you are not connected or if the connection is broken.
        """
        if self._conn is None or self._conn.closed>0:
            self._conn = connect(self._db_url)

        return self._conn.cursor()

    def __get_last_file_info(self):
        """
        Get infos about the most recently downloaded file.
        return file name and date if exists one valid download registry on log table
        """
        fname=None
        dt=None

        sql=f"""
        SELECT file_name, last_file_date FROM {self._db_schema}.{self._log_table}
        WHERE process_status = 1 ORDER BY created_at DESC LIMIT 1;
        """
        try:
            cur = self.__get_db_cursor()
            cur.execute(sql)
            results=cur.fetchall()
        except Exception as e:
            print('Error on read the file name and last date from database')
            print(e.__str__())
            raise e
        
        if len(results)>0:
            fname=results[0][0]
            dt=results[0][1]

        return fname,dt

    def __load_risk_file(self):
        """
        Read the data from the risk matrix file and load it into the temp table in the database.

        About the function to_postgis of GeoDataFrame(GeoPandas):
        https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.to_postgis.html
        """
        risk_file, file_date = self.__get_last_file_info()
        if path.isfile(risk_file):

            with rio.open(risk_file) as dataset:
                val = dataset.read(1) # band 5
                no_data=dataset.nodata
                geometry = [Point(dataset.xy(x,y)[0],dataset.xy(x,y)[1]) for x,y in np.ndindex(val.shape) if val[x,y] != no_data]
                v = [val[x,y] for x,y in np.ndindex(val.shape) if val[x,y] != no_data]
                crs = self._SRID if self._force_srid else None
                df = gpd.GeoDataFrame({'geometry':geometry,'data':v}, crs=crs)
                df.crs = dataset.crs
            # to test the results. if len of return is one its ok
            row=df.head(1)
            if len(row)==1:
                # drop the old temporary table if exists
                self.__drop_tmp_table()
                # store results
                engine = create_engine(self._db_url)
                df.to_postgis(con=engine, name=self._risk_temp_table, schema=self._db_schema, if_exists='replace', index=False)
                # create geometry index using SRID
                self.__create_index_on_tmp_table()
                # reload the points into the matrix table
                self.__populate_point_matrix()
                # copy new data to final table using Point intersects
                self.__copy_to_weekly_table(file_date)

    def __populate_point_matrix(self):
        """
        Populate the points matrix crossing the points from the temp table and the biome border.

        Prerequisites:
         - Existence of Biome Border 'deter.biome_border' as schema.table on database.
        """
        truncate=f"TRUNCATE {self._db_schema}.{self._geom_table} RESTART IDENTITY CASCADE;"
        removeindex=f"DROP INDEX {self._db_schema}.{self._db_schema}_{self._geom_table}_geom_idx;"
        insert=f"""
            INSERT INTO {self._db_schema}.{self._geom_table}(geom)
            SELECT ST_Transform(rkt.geometry,4674)
            FROM {self._db_schema}.{self._risk_temp_table} rkt, deter.biome_border bb
            WHERE ST_Intersects(ST_Transform(rkt.geometry,4674),bb.geom);
            """
        restoreindex=f"""
            CREATE INDEX {self._db_schema}_{self._geom_table}_geom_idx
                ON {self._db_schema}.{self._geom_table} USING gist (geom)
                TABLESPACE pg_default;
        """
        try:
            cur = self.__get_db_cursor()
            cur.execute(truncate)
            cur.execute(removeindex)
            cur.execute(insert)
            cur.execute(restoreindex)
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print('Error on load Points to the matrix table')
            print(e.__str__())
            raise e

    def __drop_tmp_table(self):
        """
        Remove old temp table to import new data.
        """
        drop=f"""
        DROP TABLE IF EXISTS {self._db_schema}.{self._risk_temp_table};
        """
        try:
            cur = self.__get_db_cursor()
            cur.execute(drop)
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print('Error on DROP the temporary table')
            print(e.__str__())
            raise e

    def __create_index_on_tmp_table(self):
        """
        Create a GIST index to improve copy data through intersection.
        """
        drop=f"""
        DROP INDEX IF EXISTS {self._db_schema}.{self._risk_temp_table}_geometry_idx;
        """
        add=f"""
        CREATE INDEX IF NOT EXISTS {self._risk_temp_table}_geometry_idx
        ON {self._db_schema}.{self._risk_temp_table} USING gist
        (ST_Transform(geometry,4674))
        TABLESPACE pg_default;
        """
        try:
            cur = self.__get_db_cursor()
            cur.execute(drop)
            cur.execute(add)
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print('Error on create geometry index on temporary table')
            print(e.__str__())
            raise e

    def __copy_to_weekly_table(self, file_date:datetime):
        """
        Copy the risk data into the weekly table using the pre-extracted dot matrix for the Amazon biome.

        The weekly table is cleaned by the truncate cascade over geometry table with dot matrix.

        Filter only values greater than zero.
        """
        has_new, rsktime_id = self.__has_new_risk(file_date=file_date)
        if has_new and rsktime_id is not None:
            dropindex=f"DROP INDEX {self._db_schema}.{self._db_schema}_{self._risk_input_table}_date_idx;"
            insert=f"""
            INSERT INTO {self._db_schema}.{self._risk_input_table} (date_id,geom_id,risk)
            SELECT {rsktime_id}, geom.id, rkt.data
            FROM {self._db_schema}.{self._risk_temp_table} rkt, {self._db_schema}.{self._geom_table} geom
            WHERE ST_Equals(ST_Transform(rkt.geometry,4674), geom.geom)
            AND rkt.data > 0.0;
            """
            restoreindex=f"""
            CREATE INDEX {self._db_schema}_{self._risk_input_table}_date_idx
                ON {self._db_schema}.{self._risk_input_table} USING btree (date_id ASC NULLS LAST)
                TABLESPACE pg_default;
            """
            try:
                cur = self.__get_db_cursor()
                cur.execute(dropindex) 
                cur.execute(insert)
                cur.execute(restoreindex)
                self._conn.commit()
            except Exception as e:
                self._conn.rollback()
                print('Error on insert new risk on weekly data table')
                print(e.__str__())
                raise e

    def __has_new_risk(self, file_date):
        """
        Is there a new risk?

        Make sure it has the date ID that is not yet in use, filtered by expiration date.

        The expiration date is the date of the last downloaded file increased by 7 days,
        normally, or the number of days defined by the external configuration.
        """
        has_new = False
        id = None
        expiration_date=(file_date + relativedelta(days = self._ndays_of_expiration)).strftime("%Y-%m-%d")
        sql=f"""
        SELECT t1.id
        FROM {self._db_schema}.{self._risk_expiration_table} t1
        WHERE t1.expiration_date='{expiration_date}'::date
        AND NOT EXISTS
        (
            SELECT 1 FROM {self._db_schema}.{self._risk_input_table} t2
            WHERE t2.date_id=t1.id
        );
        """
        try:
            cur = self.__get_db_cursor()
            cur.execute(sql)
            results=cur.fetchall()
            if len(results)>0 and results[0][0]>0:
                has_new = True
                id = results[0][0]
        except Exception as e:
            print('Error on read id from expiration date')
            print(e.__str__())
            raise e
        
        return has_new, id

    def execute(self):
        try:
            if self._ftp:
                self._ftp.set_expiration_days(self._ndays_of_expiration)
                self._ftp.execute()
                self.__load_risk_file()
        except OperationalError as e:
            print('Error on database connection')
            print(e.__str__())
        finally:
            if self._conn:
                self._conn.close()
