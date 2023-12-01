from os import path
import rasterio
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping
from sqlalchemy import create_engine
from rasterio.mask import mask
import numpy as np
from alive_progress import alive_bar
from datetime import datetime
from ams.utils.database_utils import DatabaseUtils
from ams.utils.risk_utils import RiskUtils

class ClassifyByLandUse:
    """
    Using to crossing the input data with the land use data and group this results by Spatial Units.
    """

    def __init__(self, biome:str, db_url: str, input_tif: str, alldata=False):
        self._datapath = path.join(path.dirname(__file__), '../../data')
        self._scriptspath = path.join(path.dirname(__file__), '../../scripts')
        self._land_use_classes_fname = input_tif
        self._biome = biome
        self._pixel_land_use_area = 29.875 * 29.875 * (10 ** -6)
        self._alldata = alldata
        self._deter_table = 'deter.tmp_data'
        self._fires_input_table = 'fires.active_fires'
        self._risk_geom_table = 'risk.matrix_ibama_1km'
        # The public.last_risk_data is an SQLView in public schema to join some tables from risk schema
        self._risk_input_table = 'public.last_risk_data'
        # temporary table prefix
        self._prefix = 'tmp'

        self._engine = create_engine(url=db_url)
        self._db = DatabaseUtils(db_url=db_url)
        self._ru = RiskUtils(db=self._db)

        # used to avoid uneeded risk processing
        self._nrp = self.__need_risk_process()

        # The class name is fixed to 'RK' as is all code that checks the risk class name.
        self._risk_classname = 'RK'
        # The class name is fixed to 'AF' as is all code that checks the fire class name.
        self._fire_classname = 'AF'

    def read_spatial_units(self):
        """
        Gets the spatial units from database.
        Prerequisites:
         - The public.spatial_units table must exist in the database and have data.
        See the README.md file for instructions.
        """
        self._spatial_units = {}
        sql = "SELECT dataname, as_attribute_name FROM public.spatial_units"
        cur = self._db.get_db_cursor()
        cur.execute(sql)
        results=cur.fetchall()
        self._spatial_units=dict(results)

    def reset_land_use_tables(self, isTemp=False):
        """
        Using DROP and CREATE table to clean old processed data.
        
        Optional parameters:
        -------------------------------------------------
        :param boolean isTemp: If Treu, use the prefix to change name to temporary or final objects on database
        """
        for spatial_unit in self._spatial_units.keys():
            if isTemp: spatial_unit=f"{self._prefix}_{spatial_unit}"
            print(f'Reset {spatial_unit}_land_use table')
            self._recreate_spatial_table(spatial_unit)

    def add_index_land_use_tables(self, isTemp=False):
        """
        Used to create the indexes into land use tables.
        
        Optional parameters:
        -------------------------------------------------
        :param boolean isTemp: If True, use the prefix to change name to temporary or final objects on database
        """
        for spatial_unit in self._spatial_units.keys():
            if isTemp: spatial_unit=f"{self._prefix}_{spatial_unit}"
            print(f'Create {spatial_unit}_land_use indexes')
            self._recreate_spatial_table_index(spatial_unit)

    def process_deter_land_structure(self):
        print(f"Creating and filling {self._prefix}_deter_land_structure.")
        cur = self._db.get_db_cursor()
        cur.execute(f"""
        DROP TABLE IF EXISTS {self._prefix}_deter_land_structure;
        CREATE TABLE IF NOT EXISTS {self._prefix}_deter_land_structure (
            id serial NOT NULL,
            gid varchar NULL,
            land_use_id int4 NULL,
            num_pixels int4 NULL,
            CONSTRAINT {self._prefix}_deter_land_structure_id_pk PRIMARY KEY (id)
        );
        """)
        
        landuse_raster = rasterio.open(f'{self._datapath}/{self._land_use_classes_fname}')
        deter = gpd.GeoDataFrame.from_postgis(sql=f'SELECT gid, geom FROM {self._deter_table}', con=self._engine)
        with alive_bar(len(deter)) as bar:
            for _, row in deter.iterrows():
                geoms = [mapping(row.geom)]
                out_image, out_transform = mask(landuse_raster, geoms, crop=True)
                unique, counts = np.unique(out_image[0], return_counts=True)
                unique_counts = np.asarray((unique, counts)).T
                counts = pd.DataFrame(unique_counts)
                for _, count in counts.iterrows():
                    if count[0] > 0:
                        cur.execute(
                            f"INSERT INTO {self._prefix}_deter_land_structure (gid, land_use_id, num_pixels) "
                            f"VALUES('{row.gid}', {count[0]}, {count[1]})")
                bar()
        
        cur.execute(f"""CREATE INDEX IF NOT EXISTS {self._prefix}_deter_land_structure_gid_idx
                    ON {self._prefix}_deter_land_structure USING hash (gid);""")

    def copy_deter_land_structure(self):
        print(f'Copy data from {self._prefix}_deter_land_structure to deter_land_structure.')
        cur = self._db.get_db_cursor()
        if self._alldata:
            cur.execute("""
            DROP TABLE IF EXISTS deter_land_structure;
            CREATE TABLE IF NOT EXISTS deter_land_structure (
                id serial NOT NULL,
                gid varchar NULL,
                land_use_id int4 NULL,
                num_pixels int4 NULL,
                CONSTRAINT deter_poly_classes_pk PRIMARY KEY (id)
            );
            """)
        else:
            # here, we expect deter.tmp_data to only have DETER data coming from the current table
            cur.execute("DELETE FROM deter_land_structure WHERE gid like '%_curr';")
            # update sequence value from the mas of table id
            cur.execute("SELECT setval('public.deter_land_structure_id_seq', (SELECT MAX(id) FROM public.deter_land_structure)::integer, true);")
        
        # copy data from temporary table
        cur.execute(f"INSERT INTO deter_land_structure (gid, land_use_id, num_pixels) "
                    f"SELECT gid, land_use_id, num_pixels FROM {self._prefix}_deter_land_structure")
        # if table is dropped, recreate index
        cur.execute("CREATE INDEX IF NOT EXISTS deter_land_structure_gid_idx ON deter_land_structure USING hash (gid);")

    def process_fires_land_structure(self):
        print(f'Creating and filling {self._prefix}_fires_land_structure.')
        
        fires_where = ""
        cur = self._db.get_db_cursor()

        if self._alldata:
            cur.execute(f"""
            DROP TABLE IF EXISTS public.{self._prefix}_fires_land_structure;
            CREATE TABLE IF NOT EXISTS {self._prefix}_fires_land_structure (
                id serial NOT NULL,
                gid integer NOT NULL,
                land_use_id int4 NULL,
                num_pixels int4 NULL,
                CONSTRAINT {self._prefix}_fires_land_structure_pk PRIMARY KEY (id)
            );
            """)
        else:
            fires_where = f""" WHERE view_date > (SELECT MAX(date) FROM "{list(self._spatial_units.keys())[0]}_land_use" WHERE classname={self._fire_classname})"""
        
        # crossing fires and raster land use data
        landuse_raster = rasterio.open(f'{self._datapath}/{self._land_use_classes_fname}')
        fires = gpd.GeoDataFrame.from_postgis(sql=f'SELECT id as gid, geom FROM {self._fires_input_table} {fires_where}', con=self._engine)
        coord_list = [(x,y) for x,y in zip(fires['geom'].x , fires['geom'].y)]
        fires['value'] = [x for x in landuse_raster.sample(coord_list)]
        with alive_bar(len(fires)) as bar:
            for _, point in fires.iterrows():
                if point['value'][0] > 0:
                    cur.execute(
                        f"INSERT INTO {self._prefix}_fires_land_structure (gid, land_use_id, num_pixels) "
                        f"VALUES('{point.gid}', {point['value'][0]}, 1)")
                bar()
        
        cur.execute(f"""CREATE INDEX IF NOT EXISTS {self._prefix}_fires_land_structure_gid_idx
                    ON public.{self._prefix}_fires_land_structure USING hash (gid);""")


    def copy_fires_land_structure(self):
        print(f'Copy data from {self._prefix}_fires_land_structure to fires_land_structure.')
        
        cur = self._db.get_db_cursor()

        if self._alldata:
            cur.execute(f"""
            DROP TABLE IF EXISTS public.fires_land_structure;
            CREATE TABLE IF NOT EXISTS fires_land_structure (
                id serial NOT NULL,
                gid integer NOT NULL,
                land_use_id int4 NULL,
                num_pixels int4 NULL,
                CONSTRAINT fires_land_structure_pk PRIMARY KEY (id)
            );
            """)
        
        # copy data from temporary table
        cur.execute(f"INSERT INTO fires_land_structure (gid, land_use_id, num_pixels) "
                    f"SELECT gid, land_use_id, num_pixels FROM {self._prefix}_fires_land_structure")
        # if table is dropped, recreate index
        cur.execute("CREATE INDEX IF NOT EXISTS fires_land_structure_gid_idx ON fires_land_structure USING hash (gid);")

    def process_risk_land_structure(self):
        """
        Crossing the point matrix from risk data with land use raster data.

        Only perform this step if we have new risk data.

        Its DROP and CREATE the tmp_risk_land_structure table
        """
        print(f'Creating and filling {self._prefix}_risk_land_structure.')
        
        cur = self._db.get_db_cursor()

        cur.execute(f"""
        DROP TABLE IF EXISTS public.{self._prefix}_risk_land_structure;
        CREATE TABLE IF NOT EXISTS {self._prefix}_risk_land_structure (
            id serial NOT NULL,
            gid integer NOT NULL,
            land_use_id int4 NULL,
            num_pixels int4 NULL,
            CONSTRAINT {self._prefix}_risk_land_structure_pk PRIMARY KEY (id)
        );""")
        
        # crossing risk and raster land use data
        landuse_raster = rasterio.open(f'{self._datapath}/{self._land_use_classes_fname}')
        
        risk = gpd.GeoDataFrame.from_postgis(sql=f'SELECT id as gid, geom FROM {self._risk_geom_table} ', con=self._engine)
        coord_list = [(x,y) for x,y in zip(risk['geom'].x , risk['geom'].y)]
        risk['value'] = [x for x in landuse_raster.sample(coord_list)]
        with alive_bar(len(risk)) as bar:
            for _, point in risk.iterrows():
                if point['value'][0] > 0:
                    cur.execute(
                        f"INSERT INTO {self._prefix}_risk_land_structure (gid, land_use_id, num_pixels) "
                        f"VALUES('{point.gid}', {point['value'][0]}, 1)")
                bar()
        # create index
        cur.execute(f"""CREATE INDEX IF NOT EXISTS {self._prefix}_risk_land_structure_gid_idx
                        ON public.{self._prefix}_risk_land_structure USING hash (gid);""")

    def copy_risk_land_structure(self):
        print(f'Copy data from {self._prefix}_risk_land_structure to risk_land_structure.')
        
        cur = self._db.get_db_cursor()

        cur.execute(f"""
        DROP TABLE IF EXISTS public.risk_land_structure;
        CREATE TABLE IF NOT EXISTS risk_land_structure (
            id serial NOT NULL,
            gid integer NOT NULL,
            land_use_id int4 NULL,
            num_pixels int4 NULL,
            CONSTRAINT risk_land_structure_pk PRIMARY KEY (id)
        );""")
        
        # copy data from temporary table
        cur.execute(f"INSERT INTO risk_land_structure (gid, land_use_id, num_pixels) "
                    f"SELECT gid, land_use_id, num_pixels FROM {self._prefix}_risk_land_structure")
        # if table is dropped, recreate index
        cur.execute(f"""
        CREATE INDEX IF NOT EXISTS risk_land_structure_gid_idx ON public.risk_land_structure USING hash (gid);""")

    def _recreate_spatial_table(self, spatial_unit):
        """
        Even if "alldata" is true, we recreate the final land_use table.
        *The control is made in intermediary table called "<target_data>_land_structure"
        """
        risk_col=""
        if self._biome=="Amazônia":
            risk_col="risk double precision NOT NULL DEFAULT 0.0,"
        cur = self._db.get_db_cursor()
        cur.execute(
            f"""DROP TABLE IF EXISTS "{spatial_unit}_land_use"; 
            CREATE TABLE IF NOT EXISTS "{spatial_unit}_land_use" (
                id serial NOT NULL,
                suid int NOT NULL,
                land_use_id int NOT NULL,
                classname varchar(2) NOT NULL,
                "date" date NOT NULL,
                area double precision,
                percentage double precision,
                counts integer,
                {risk_col}
                CONSTRAINT "{spatial_unit}_land_use_pkey" PRIMARY KEY (id)
            );
            """
        )

    def _recreate_spatial_table_index(self, spatial_unit):
        """
        Create index on tables because we use drop and create to reset old results. Used after populate tables.
        """
        risk_index=""
        if self._biome=="Amazônia":
            risk_index=f"""CREATE INDEX IF NOT EXISTS "{spatial_unit}_land_use_risk_idx" ON "{spatial_unit}_land_use"
            USING btree (risk ASC NULLS LAST);"""
        cur = self._db.get_db_cursor()
        cur.execute(
            f"""
            CREATE INDEX IF NOT EXISTS "{spatial_unit}_land_use_classname_idx" ON "{spatial_unit}_land_use"
            USING btree (classname ASC NULLS LAST);
            CREATE INDEX IF NOT EXISTS "{spatial_unit}_land_use_date_idx" ON "{spatial_unit}_land_use"
            USING btree (date DESC NULLS LAST);
            {risk_index}
            """
        )

    def insert_deter_in_land_use_tables(self):
        print('Insert DETER data in land use tables for each spatial units.')
        cur = self._db.get_db_cursor()
        
        land_structure = gpd.GeoDataFrame.from_postgis(sql=f""" 
        SELECT a.id, a.land_use_id, a.num_pixels, d.name as classname, b.date, b.geom as geometry
        FROM {self._prefix}_deter_land_structure a 
        INNER JOIN 
        (SELECT tb.gid, tb.date, ST_PointOnSurface(tb.geom) as geom, tb.classname
        FROM (
            SELECT gid, date, classname, geom
            FROM deter.deter_auth
            UNION
            SELECT gid, date, classname, geom
            FROM deter.deter_history
        ) as tb) b 
        ON a.gid = b.gid
        INNER JOIN deter_class c 
        ON b.classname = c.name
        INNER JOIN deter_class_group d
        ON c.group_id = d.id """, con=self._engine, geom_col='geometry')
        for spatial_unit in self._spatial_units.keys():
            tmpspatial_unit=f"{self._prefix}_{spatial_unit}"
            print(f'Processing {tmpspatial_unit}...')
            spatial_units = gpd.GeoDataFrame.from_postgis(
                sql=f'SELECT suid, geometry FROM "{spatial_unit}"',
                con=self._engine, geom_col='geometry')
            print('Joining...')
            join = gpd.sjoin(land_structure, spatial_units, how='inner', op='intersects')
            print('Grouping...')
            group = join[['suid', 'land_use_id', 'classname', 'date', 'num_pixels']].groupby(
                ['suid', 'land_use_id', 'classname','date'])['num_pixels'].sum()

            with alive_bar(len(group)) as bar:
                for key, value in group.items():
                    cur.execute(
                    f"""INSERT INTO "{tmpspatial_unit}_land_use" (suid, land_use_id, classname, "date", area) 
                    VALUES({key[0]}, {key[1]}, '{key[2]}', TIMESTAMP 
                    '{key[3].year}-{key[3].month}-{key[3].day}',{value * self._pixel_land_use_area});""")
                    bar()

    def insert_fires_in_land_use_tables(self):
        print('Insert active fires in land use tables for each spatial units.')
        cur = self._db.get_db_cursor()
        
        land_structure = gpd.GeoDataFrame.from_postgis(sql=f""" 
        SELECT a.id,a.land_use_id,a.num_pixels,{self._fire_classname} as classname,b.view_date as date,b.geom as geometry
        FROM {self._prefix}_fires_land_structure a 
        INNER JOIN {self._fires_input_table} b 
        ON a.gid = b.id""", con=self._engine, geom_col='geometry')
        for spatial_unit in self._spatial_units.keys():
            tmpspatial_unit=f"{self._prefix}_{spatial_unit}"
            print(f'Processing {tmpspatial_unit}...')
            spatial_units = gpd.GeoDataFrame.from_postgis(
                sql=f'SELECT suid, geometry FROM "{spatial_unit}"',
                con=self._engine, geom_col='geometry')
            print('Joining...')
            join = gpd.sjoin(land_structure, spatial_units, how='inner', op='intersects')
            print('Grouping...')
            group = join[['suid', 'land_use_id', 'classname', 'date', 'num_pixels']].groupby(
                ['suid', 'land_use_id', 'classname','date'])['num_pixels'].sum()
            
            with alive_bar(len(group)) as bar:
                for key, value in group.items():
                    cur.execute(
                    f"""INSERT INTO "{tmpspatial_unit}_land_use" (suid, land_use_id, classname, "date", counts) 
                    VALUES({key[0]}, {key[1]}, '{key[2]}', TIMESTAMP 
                    '{key[3].year}-{key[3].month}-{key[3].day}',{value});""")
                    bar()

    def insert_risk_in_land_use_tables(self):
        """
        Join and group the temporary land structure table data with the spatial units to populate the temporary land use tables with risk.
        """
        print('Insert ibama risk in land use tables for each spatial units.')
        cur = self._db.get_db_cursor()
        
        land_structure = gpd.GeoDataFrame.from_postgis(sql=f""" 
        SELECT a.id, a.land_use_id, a.num_pixels, {self._risk_classname} as classname, b.risk, b.view_date as date, b.geom as geometry
        FROM {self._prefix}_risk_land_structure a 
        INNER JOIN {self._risk_input_table} b 
        ON a.gid = b.id""", con=self._engine, geom_col='geometry')
        for spatial_unit in self._spatial_units.keys():
            tmpspatial_unit=f"{self._prefix}_{spatial_unit}"
            print(f'Processing {tmpspatial_unit}...')
            spatial_units = gpd.GeoDataFrame.from_postgis(
                sql=f'SELECT suid, geometry FROM "{spatial_unit}"',
                con=self._engine, geom_col='geometry')
            print('Joining...')
            join = gpd.sjoin(land_structure, spatial_units, how='inner', op='intersects')
            print('Grouping...')
            group = join[['suid', 'land_use_id', 'classname', 'date', 'risk', 'num_pixels']].groupby(
                ['suid', 'land_use_id', 'classname','date', 'risk'])['num_pixels'].sum()

            with alive_bar(len(group)) as bar:
                for key, value in group.items():
                    cur.execute(
                    f"""INSERT INTO "{tmpspatial_unit}_land_use" (suid, land_use_id, classname, "date", risk, counts) 
                    VALUES({key[0]}, {key[1]}, '{key[2]}', TIMESTAMP 
                    '{key[3].year}-{key[3].month}-{key[3].day}', {key[4]},{value});""")
                    bar()

    def percentage_calculation_for_areas(self):
        print('Using Spatial Units areas and DETER areas to calculate percentage.')
        cur = self._db.get_db_cursor()
        for spatial_unit in self._spatial_units.keys():
            tmpspatial_unit=f"{self._prefix}_{spatial_unit}"
            print(f'Processing {tmpspatial_unit}...')
            cur.execute(
            f"""UPDATE public."{tmpspatial_unit}_land_use"
            SET percentage=public."{tmpspatial_unit}_land_use".area/su.area*100
            FROM public."{spatial_unit}" su WHERE public."{tmpspatial_unit}_land_use".suid=su.suid
            AND public."{tmpspatial_unit}_land_use".classname NOT IN ({self._fire_classname},{self._risk_classname}) """)
    
    def copy_data_to_final_tables(self):
        print('Copy the new processed data to the final tables.')
        self.copy_deter_land_structure()
        self.copy_fires_land_structure()
        risk_column=""
        if self._nrp:
            self.copy_risk_land_structure()
            risk_column=", risk"

        cur = self._db.get_db_cursor()
        for spatial_unit in self._spatial_units.keys():
            tmpspatial_unit=f"{self._prefix}_{spatial_unit}"
            print(f'Copy from {tmpspatial_unit} to {spatial_unit}')
            cur.execute(
            f"""INSERT INTO "{spatial_unit}_land_use" (suid, land_use_id, classname, "date", area, percentage, counts {risk_column})
            SELECT suid, land_use_id, classname, date, area, percentage, counts {risk_column} FROM
            "{tmpspatial_unit}_land_use"
            """)

    def __need_risk_process(self):
        """
        Do we need risk processing? Only if is in Amazonia database.

        Responds true if there is new risk data that has not yet been processed.
        """

        if self._biome!="Amazônia":
            return False

        risk_file, risk_date = self._ru.get_last_file_info()
        is_new = self._ru.second_phase_already(risk_date=risk_date)

        return (path.isfile(risk_file) and is_new)

    def execute(self):
        try:
            print("Starting at: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
            self.read_spatial_units()
            # Drop temporary tables to process data without blocking database resources
            self.reset_land_use_tables(isTemp=True)
            self.process_deter_land_structure()
            self.process_fires_land_structure()
            # we need commit this results because the next step open a new conection with database
            self._db.commit()
            print("Time control after process deter and fires in land structure tables: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))

            self.insert_deter_in_land_use_tables()
            self.insert_fires_in_land_use_tables()
            self._db.commit()
            print("Time control after insert deter and fires in land use tables: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))

            if self._nrp:
                self.process_risk_land_structure()
                # we need commit this results because the next step open a new conection with database
                self._db.commit()
                print("Time control after process risk in land structure table: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
                self.insert_risk_in_land_use_tables()
            
            print("Time control after process all using temp tables: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
            self.add_index_land_use_tables(isTemp=True)
            self.percentage_calculation_for_areas()
            self._db.commit()
            print("Time control after commit on temp tables: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))

            # Drop operational tables to copy new data
            self.reset_land_use_tables(isTemp=False)
            self.copy_data_to_final_tables()
            self.add_index_land_use_tables(isTemp=False)
            self._db.commit()
            print("Finished in: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
        except Exception as e:
            self._db.rollback()
            print('Error on classify by land_structure, deter and fires')
            print(e.__str__())
            raise e
        finally:
            self._db.close()
