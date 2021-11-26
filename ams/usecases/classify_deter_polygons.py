# https://zoomadmin.com/HowToInstall/UbuntuPackage/libspatialindex-dev
import sys
from os import path
from psycopg2 import connect
import rasterio
import geopandas as gpd
import pygeos
import rtree
import pandas as pd
from shapely.geometry import mapping
from rasterio.mask import mask
import numpy as np
from alive_progress import alive_bar
import time
from datetime import timedelta

class ClassifyDeterPolygons:
    """ClassifyDeterPolygons"""

    def __init__(self, db_url: str):
        self._datapath = path.join(path.dirname(__file__), '../../data')
        self._scriptspath = path.join(path.dirname(__file__), '../../scripts')
        self._amazon_class_fname = 'est_fundiaria_cst.tif'
        self._conn = connect(db_url)
        self._spatial_units = {'csAmz_150km': 'id','csAmz_300km': 'id',
                               'amz_municipalities': 'nm_municip',
                               'amz_states': 'NM_ESTADO'}
        self._pixel_land_use_area = 29.875 * 29.875 * (10 ** -6)

    def create_land_use_table(self):
        with open(f'{self._scriptspath}/fill_land_use.sql', encoding='UTF-8') as scriptfile:
            script = scriptfile.read()
            cur = self._conn.cursor()
            cur.execute(script)

    def process_deter_land_strucure(self):
        print('Creating and filling deter_land_structure.')
        cur = self._conn.cursor()
        cur.execute('''
        drop table if exists deter_land_structure;
        drop sequence if exists public.deter_land_structure_id_seq;
        CREATE SEQUENCE public.deter_land_structure_id_seq
        	INCREMENT BY 1
        	MINVALUE 1
        	MAXVALUE 2147483647
        	START 1
        	CACHE 1
        	NO CYCLE;
        CREATE TABLE deter_land_structure (
        	id int4 NOT NULL DEFAULT nextval('deter_land_structure_id_seq'::regclass),
        	deter_gid varchar NULL,
        	land_use_id int4 NULL,
        	num_pixels int4 NULL,
        	CONSTRAINT deter_poly_classes_pk PRIMARY KEY (id)
        );
        CREATE INDEX deter_poly_classes_deter_gid_idx ON public.deter_land_structure USING btree (deter_gid);''')
        amazon_class = rasterio.open(f'{self._datapath}/{self._amazon_class_fname}')
        deter = gpd.GeoDataFrame.from_postgis('SELECT gid, geom FROM deter.deter_all', self._conn)
        cur = self._conn.cursor()
        i = 0
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
                            f"INSERT INTO deter_land_structure (deter_gid, land_use_id, num_pixels) "
                            f"VALUES('{row.gid}', {count[0]}, {count[1]})")
                i += 1
                if (i % 1000) == 0:
                    self._conn.commit()
                bar()
        self._conn.commit()

    def create_table(self, spatial_unit):
        cur = self._conn.cursor()
        cur.execute(f'''DROP TABLE IF EXISTS "{spatial_unit}_land_use"; 
CREATE TABLE "{spatial_unit}_land_use" (
    id serial4 NOT NULL,
    suid int NOT NULL,
	land_use_id int NOT NULL,
	classname varchar(2) NOT NULL,
	"date" date NOT NULL,
	area float8 NOT NULL,
	CONSTRAINT "{spatial_unit}_land_use_pkey" PRIMARY KEY (id)
);''')
        self._conn.commit()

    def create_land_structure_tables(self):
        print('Creating land structure/spatial units tables.')
        cur = self._conn.cursor()
        land_structure = gpd.GeoDataFrame.from_postgis(''' 
        select a.id,a.land_use_id,a.num_pixels,d.name as classname,b.date,b.geom as geometry from deter_land_structure a 
inner join deter.deter_all b 
on a.deter_gid = b.gid
inner join deter_class c 
on b.classname = c.name
inner join deter_class_group d
on c.group_id = d.id ''', self._conn, geom_col='geometry')
        for spatial_unit in self._spatial_units.keys():
            print(f'Processing {spatial_unit}...')
            self.create_table(spatial_unit)
            spatial_units = gpd.GeoDataFrame.from_postgis(
                f'select suid,st_transform(geometry, 4674) as geometry from "{spatial_unit}"',
                self._conn, geom_col='geometry')
            print('Joining...')
            join = gpd.sjoin(land_structure, spatial_units, how='inner', op='intersects')
            print('Grouping...')
            group = join[['suid', 'land_use_id', 'classname', 'date', 'num_pixels']].groupby(
                ['suid', 'land_use_id', 'classname','date'])['num_pixels'].sum()
            i = 0
            with alive_bar(len(group)) as bar:
                for key, value in group.iteritems():
                    cur.execute(
f"""INSERT INTO "{spatial_unit}_land_use" (suid, land_use_id, classname, "date", area) 
VALUES({key[0]}, {key[1]}, '{key[2]}', TIMESTAMP 
        '{key[3].year}-{key[3].month}-{key[3].day}',{value * self._pixel_land_use_area});""")
                    bar()
                    if (i % 1000) == 0:
                        self._conn.commit()
            self._conn.commit()

    def execute(self):
        self.create_land_use_table()
        self.process_deter_land_strucure()
        self.create_land_structure_tables()
