from os import path
from psycopg2 import connect
import rasterio
import geopandas as gpd
import pandas as pd
from shapely.geometry import mapping
from rasterio.mask import mask
import numpy as np
from alive_progress import alive_bar
from datetime import datetime

class ClassifyByLandUse:
    """ClassifyByLandUse"""

    def __init__(self, db_url: str, input_tif: str, alldata=False):
        self._datapath = path.join(path.dirname(__file__), '../../data')
        self._scriptspath = path.join(path.dirname(__file__), '../../scripts')
        self._amazon_class_fname = input_tif
        self._conn = connect(db_url)
        self._pixel_land_use_area = 29.875 * 29.875 * (10 ** -6)
        self._deter_table = 'deter.tmp_data' if alldata else 'deter.deter_auth'
        self._fires_input_table = 'fires.active_fires'

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

    def process_deter_land_structure(self):
        print('Creating and filling deter_land_structure.')
        cur = self._conn.cursor()
        cur.execute('''
        DROP TABLE IF EXISTS deter_land_structure;
        CREATE TABLE deter_land_structure (
        	id serial NOT NULL,
        	gid varchar NULL,
        	land_use_id int4 NULL,
        	num_pixels int4 NULL,
        	CONSTRAINT deter_poly_classes_pk PRIMARY KEY (id)
        );
        CREATE INDEX deter_land_structure_gid_idx ON public.deter_land_structure USING btree (gid);''')
        amazon_class = rasterio.open(f'{self._datapath}/{self._amazon_class_fname}')
        deter = gpd.GeoDataFrame.from_postgis(f'SELECT gid, geom FROM {self._deter_table}', self._conn)
        with alive_bar(len(deter)) as bar:
            for _, row in deter.iterrows():
                geoms = [mapping(row.geom)]
                out_image, out_transform = mask(amazon_class, geoms, crop=True)
                unique, counts = np.unique(out_image[0], return_counts=True)
                unique_counts = np.asarray((unique, counts)).T
                counts = pd.DataFrame(unique_counts)
                for _, count in counts.iterrows():
                    if count[0] > 0:
                        cur.execute(
                            f"INSERT INTO deter_land_structure (gid, land_use_id, num_pixels) "
                            f"VALUES('{row.gid}', {count[0]}, {count[1]})")
                bar()

    def process_fires_land_structure(self):
        print('Creating and filling fires_land_structure.')
        cur = self._conn.cursor()
        cur.execute('''
        DROP TABLE IF EXISTS public.fires_land_structure;
        CREATE TABLE fires_land_structure (
        	id serial NOT NULL,
        	gid integer NOT NULL,
        	land_use_id int4 NULL,
        	num_pixels int4 NULL,
        	CONSTRAINT fires_land_structure_pk PRIMARY KEY (id)
        );
        CREATE INDEX fires_land_structure_gid_idx ON public.fires_land_structure USING btree (gid);''')
        amazon_class = rasterio.open(f'{self._datapath}/{self._amazon_class_fname}')
        fires = gpd.GeoDataFrame.from_postgis(f'SELECT id as gid, geom FROM {self._fires_input_table}', self._conn)
        coord_list = [(x,y) for x,y in zip(fires['geom'].x , fires['geom'].y)]
        fires['value'] = [x for x in amazon_class.sample(coord_list)]
        with alive_bar(len(fires)) as bar:
            for _, point in fires.iterrows():
                if point['value'][0] > 0:
                    cur.execute(
                        f"INSERT INTO fires_land_structure (gid, land_use_id, num_pixels) "
                        f"VALUES('{point.gid}', {point['value'][0]}, 1)")
                bar()

    def _create_table(self, spatial_unit):
        cur = self._conn.cursor()
        cur.execute(f'''DROP TABLE IF EXISTS "{spatial_unit}_land_use"; 
        CREATE TABLE "{spatial_unit}_land_use" (
            id serial NOT NULL,
            suid int NOT NULL,
            land_use_id int NOT NULL,
            classname varchar(2) NOT NULL,
            "date" date NOT NULL,
            area double precision,
            counts integer,
            CONSTRAINT "{spatial_unit}_land_use_pkey" PRIMARY KEY (id)
        );''')

    def create_land_structure_tables(self):
        print('Creating land structure/spatial units tables.')
        cur = self._conn.cursor()
        land_structure = gpd.GeoDataFrame.from_postgis(f''' 
        SELECT a.id,a.land_use_id,a.num_pixels,d.name as classname,b.date,b.geom as geometry
        FROM deter_land_structure a 
        INNER JOIN {self._deter_table} b 
        ON a.gid = b.gid
        INNER JOIN deter_class c 
        ON b.classname = c.name
        INNER JOIN deter_class_group d
        ON c.group_id = d.id ''', self._conn, geom_col='geometry')
        for spatial_unit in self._spatial_units.keys():
            print(f'Processing {spatial_unit}...')
            self._create_table(spatial_unit)
            spatial_units = gpd.GeoDataFrame.from_postgis(
                f'SELECT suid, geometry FROM "{spatial_unit}"',
                self._conn, geom_col='geometry')
            print('Joining...')
            join = gpd.sjoin(land_structure, spatial_units, how='inner', op='intersects')
            print('Grouping...')
            group = join[['suid', 'land_use_id', 'classname', 'date', 'num_pixels']].groupby(
                ['suid', 'land_use_id', 'classname','date'])['num_pixels'].sum()

            with alive_bar(len(group)) as bar:
                for key, value in group.iteritems():
                    cur.execute(
                    f"""INSERT INTO "{spatial_unit}_land_use" (suid, land_use_id, classname, "date", area) 
                    VALUES({key[0]}, {key[1]}, '{key[2]}', TIMESTAMP 
                    '{key[3].year}-{key[3].month}-{key[3].day}',{value * self._pixel_land_use_area});""")
                    bar()

    def insert_fires_in_land_structure_tables(self):
        print('insert active fires in land structure tables for each spatial units.')
        cur = self._conn.cursor()
        land_structure = gpd.GeoDataFrame.from_postgis(f''' 
        SELECT a.id,a.land_use_id,a.num_pixels,'AF' as classname,b.view_date as date,b.geom as geometry
        FROM fires_land_structure a 
        INNER JOIN {self._fires_input_table} b 
        ON a.gid = b.id''', self._conn, geom_col='geometry')
        for spatial_unit in self._spatial_units.keys():
            print(f'Processing {spatial_unit}...')
            spatial_units = gpd.GeoDataFrame.from_postgis(
                f'SELECT suid, geometry FROM "{spatial_unit}"',
                self._conn, geom_col='geometry')
            print('Joining...')
            join = gpd.sjoin(land_structure, spatial_units, how='inner', op='intersects')
            print('Grouping...')
            group = join[['suid', 'land_use_id', 'classname', 'date', 'num_pixels']].groupby(
                ['suid', 'land_use_id', 'classname','date'])['num_pixels'].sum()

            with alive_bar(len(group)) as bar:
                for key, value in group.iteritems():
                    cur.execute(
                    f"""INSERT INTO "{spatial_unit}_land_use" (suid, land_use_id, classname, "date", counts) 
                    VALUES({key[0]}, {key[1]}, '{key[2]}', TIMESTAMP 
                    '{key[3].year}-{key[3].month}-{key[3].day}',{value});""")
                    bar()

    def execute(self):
        try:
            print("Starting at: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
            self.read_spatial_units()
            self.process_deter_land_structure()
            self.process_fires_land_structure()
            self.create_land_structure_tables()
            self.insert_fires_in_land_structure_tables()
            print("Finished in: "+datetime.now().strftime("%d/%m/%YT%H:%M:%S"))
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print('Error on classify by land_structure, deter and fires')
            print(e.__str__())
            raise e
