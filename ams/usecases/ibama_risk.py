from os import path
from psycopg2 import OperationalError
import geopandas as gpd
from sqlalchemy import create_engine
import rasterio as rio
from shapely.geometry import Point
import numpy as np
from ams.dataaccess.ftp_ibama_risk import FtpIBAMARisk
from ams.utils.database_utils import DatabaseUtils
from ams.utils.risk_utils import RiskUtils
from ams.config import Config


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
        self._db = DatabaseUtils(db_url=db_url)

        # About Risk
        self._ru = RiskUtils(db=self._db)

        # risk model database entities
        self._db_schema = 'risk'
        self._risk_input_table = 'weekly_data'
        self._geom_table = 'matrix_ibama_1km'
        self._risk_temp_table = 'weekly_ibama_tmp'
        self._risk_threshold = Config.RISK_THRESHOLD_DB

        # input data configuration
        self._SRID = srid if srid is not None else srid
        self._force_srid = force_srid

        # number of days to set the risk forecast due date
        self._ndays_of_expiration = expiration_risk

    def __load_risk_file(self):
        """
        Read the data from the risk matrix file and load it into the temp table in the database.

        About the function to_postgis of GeoDataFrame(GeoPandas):
        https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.to_postgis.html
        """
        risk_file, risk_date = self._ru.get_last_file_info()
        is_new, risk_time_id = self._ru.first_phase_already(risk_date=risk_date)

        if path.isfile(risk_file) and is_new and risk_time_id is not None:

            with rio.open(risk_file) as dataset:
                val = dataset.read(1) # band 5
                
                indices = np.where(val > self._risk_threshold)
                indices = list(zip(indices[0], indices[1]))
                
                geometry = [Point(dataset.xy(x,y)[0], dataset.xy(x,y)[1]) for x, y in indices]
                v = [val[x,y] for x, y in indices]
                
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
                self.__copy_to_weekly_table(risk_time_id=risk_time_id)

    def __populate_point_matrix(self):
        """
        Populate the points matrix crossing the points from the temp table and the biome border.

        Prerequisites:
         - Existence of Biome Border 'deter.biome_border' as schema.table on database.
        """
        truncate=f"TRUNCATE {self._db_schema}.{self._geom_table} RESTART IDENTITY CASCADE;"
        removeindex=f"DROP INDEX IF EXISTS {self._db_schema}.{self._db_schema}_{self._geom_table}_geom_idx;"
        insert=f"""
            INSERT INTO {self._db_schema}.{self._geom_table}(geom)
            SELECT ST_Transform(rkt.geometry,4674)
            FROM {self._db_schema}.{self._risk_temp_table} rkt, deter.biome_border bb
            WHERE ST_Intersects(ST_Transform(rkt.geometry,4674),bb.geom);
            """
        restoreindex=f"""
            CREATE INDEX IF NOT EXISTS {self._db_schema}_{self._geom_table}_geom_idx
                ON {self._db_schema}.{self._geom_table} USING gist (geom)
                TABLESPACE pg_default;
        """
        try:
            cur = self._db.get_db_cursor()
            cur.execute(truncate)
            cur.execute(removeindex)
            cur.execute(insert)
            cur.execute(restoreindex)
            self._db.commit()
        except Exception as e:
            self._db.rollback()
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
            cur = self._db.get_db_cursor()
            cur.execute(drop)
            self._db.commit()
        except Exception as e:
            self._db.rollback()
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
            cur = self._db.get_db_cursor()
            cur.execute(drop)
            cur.execute(add)
            self._db.commit()
        except Exception as e:
            self._db.rollback()
            print('Error on create geometry index on temporary table')
            print(e.__str__())
            raise e

    def __copy_to_weekly_table(self, risk_time_id:str):
        """
        Copy the risk data into the weekly table using the pre-extracted dot matrix for the Amazon biome.

        The weekly table is cleaned by the truncate cascade over geometry table with dot matrix.

        Filter only values greater than zero.
        """
        dropindex=f"DROP INDEX {self._db_schema}.{self._db_schema}_{self._risk_input_table}_date_idx;"
        insert=f"""
        INSERT INTO {self._db_schema}.{self._risk_input_table} (date_id,geom_id,risk)
        SELECT {risk_time_id}, geom.id, rkt.data
        FROM {self._db_schema}.{self._risk_temp_table} rkt, {self._db_schema}.{self._geom_table} geom
        WHERE ST_Equals(ST_Transform(rkt.geometry,4674), geom.geom);
        """
        restoreindex=f"""
        CREATE INDEX {self._db_schema}_{self._risk_input_table}_date_idx
            ON {self._db_schema}.{self._risk_input_table} USING btree (date_id ASC NULLS LAST)
            TABLESPACE pg_default;
        """
        try:
            cur = self._db.get_db_cursor()
            cur.execute(dropindex) 
            cur.execute(insert)
            cur.execute(restoreindex)
            self._db.commit()
        except Exception as e:
            self._db.rollback()
            print('Error on insert new risk on weekly data table')
            print(e.__str__())
            raise e

    def execute(self):
        try:
            if self._ftp:
                self._ftp.set_expiration_days(self._ndays_of_expiration)
                self._ftp.execute()
                self.__load_risk_file()
        except OperationalError as e:
            print('Error on database connection')
            print(e.__str__())
        except Exception as e:
            print('Error in processing risk data')
            print(e.__str__())
        finally:
            self._db.close()
