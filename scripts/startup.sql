-- -------------------------------------------------------------------------
-- To create the database model, run it in the separate SQL Query window
-- connected into AMS database already created.
-- WARNING: Change the dblink properties before run
-- -------------------------------------------------------------------------

BEGIN;

-- -------------------------------------------------------------------------
-- Required database extensions
-- -------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS dblink;

-- -------------------------------------------------------------------------
-- This session is used for pointing to DETER and Active Fires databases using SQL Views via dblink
-- -------------------------------------------------------------------------

-- WARNING: Change the dblink properties to pointing to real DETER database.
-- WARNING: Change the dblink properties to pointing to real Active Fires database.

-- Find this line and properly change each one
-- hostaddr=<IP or hostname> port=5432 dbname=<DB_NAME> user=postgres password=postgres'

-- -------------------------------------------------------------------------
-- View: public.deter

-- DROP VIEW public.deter;

CREATE OR REPLACE VIEW public.deter
 AS
 SELECT remote_data.gid,
    remote_data.origin_gid,
    remote_data.classname,
    remote_data.quadrant,
    remote_data.orbitpoint,
    remote_data.date,
    remote_data.sensor,
    remote_data.satellite,
    remote_data.areatotalkm,
    remote_data.areamunkm,
    remote_data.areauckm,
    remote_data.mun,
    remote_data.uf,
    remote_data.uc,
    remote_data.geom,
    remote_data.month_year
   FROM dblink('hostaddr=<IP or hostname> port=5432 dbname=<DB_NAME> user=postgres password=postgres'::text, 'SELECT gid, origin_gid, classname, quadrant, orbitpoint, date, sensor, satellite, areatotalkm, areamunkm, areauckm, mun, uf, uc, geom, month_year FROM public.deter_ams'::text) remote_data(gid text, origin_gid integer, classname character varying(254), quadrant character varying(5), orbitpoint character varying(10), date date, sensor character varying(10), satellite character varying(13), areatotalkm double precision, areamunkm double precision, areauckm double precision, mun character varying(254), uf character varying(2), uc character varying(254), geom geometry(MultiPolygon,4674), month_year character varying(10));

-- View: public.deter_auth

-- DROP VIEW public.deter_auth;

CREATE OR REPLACE VIEW public.deter_auth
 AS
 SELECT remote_data.gid,
    remote_data.origin_gid,
    remote_data.classname,
    remote_data.quadrant,
    remote_data.orbitpoint,
    remote_data.date,
    remote_data.sensor,
    remote_data.satellite,
    remote_data.areatotalkm,
    remote_data.areamunkm,
    remote_data.areauckm,
    remote_data.mun,
    remote_data.uf,
    remote_data.uc,
    remote_data.geom,
    remote_data.month_year
   FROM dblink('hostaddr=<IP or hostname> port=5432 dbname=<DB_NAME> user=postgres password=postgres'::text, 'SELECT gid, origin_gid, classname, quadrant, orbitpoint, date, sensor, satellite, areatotalkm, areamunkm, areauckm, mun, uf, uc, geom, month_year FROM public.deter_auth_ams'::text) remote_data(gid text, origin_gid integer, classname character varying(254), quadrant character varying(5), orbitpoint character varying(10), date date, sensor character varying(10), satellite character varying(13), areatotalkm double precision, areamunkm double precision, areauckm double precision, mun character varying(254), uf character varying(2), uc character varying(254), geom geometry(MultiPolygon,4674), month_year character varying(10));


-- View: public.deter_history

-- DROP VIEW public.deter_history;

CREATE OR REPLACE VIEW public.deter_history
 AS
 SELECT remote_data.gid,
    remote_data.origin_gid,
    remote_data.classname,
    remote_data.quadrant,
    remote_data.orbitpoint,
    remote_data.date,
    remote_data.sensor,
    remote_data.satellite,
    remote_data.areatotalkm,
    remote_data.areamunkm,
    remote_data.areauckm,
    remote_data.mun,
    remote_data.uf,
    remote_data.uc,
    remote_data.geom,
    remote_data.month_year
   FROM dblink('hostaddr=<IP or hostname> port=5432 dbname=<DB_NAME> user=postgres password=postgres'::text, '
			   SELECT id as gid, gid as origin_gid, classname, quadrant, orbitpoint, date,
                sensor, satellite, areatotalkm, areamunkm, areauckm, county as mun, uf, uc,
                st_multi(geom)::geometry(MultiPolygon,4674) AS geom,
                to_char(timezone(''UTC''::text, date::timestamp with time zone), ''MM-YYYY''::text) AS month_year
                FROM public.deter_history WHERE areatotalkm>=0.01
			   '::text) remote_data(gid text, origin_gid integer, classname character varying(254), quadrant character varying(5), orbitpoint character varying(10), date date, sensor character varying(10), satellite character varying(13), areatotalkm double precision, areamunkm double precision, areauckm double precision, mun character varying(254), uf character varying(2), uc character varying(254), geom geometry(MultiPolygon,4674), month_year character varying(10));


-- View: public.deter_aggregated_ibama

-- DROP VIEW public.deter_aggregated_ibama;

CREATE OR REPLACE VIEW public.deter_aggregated_ibama
 AS
 SELECT remote_data.origin_gid,
    remote_data.date,
    remote_data.areamunkm,
    remote_data.classname,
    remote_data.ncar_ids,
    remote_data.car_imovel,
    remote_data.continuo,
    remote_data.velocidade,
    remote_data.deltad,
    remote_data.est_fund,
    remote_data.dominio,
    remote_data.tp_dominio
   FROM dblink('hostaddr=<IP or hostname> port=5432 dbname=<DB_NAME> user=postgres password=postgres'::text, 'SELECT origin_gid, view_date as date, areamunkm, classname, ncar_ids, car_imovel, continuo, velocidade, deltad, est_fund, dominio, tp_dominio FROM deter_agregate.deter WHERE areatotalkm>=0.01 AND uf<>''MS'' AND source=''D'''::text) remote_data(origin_gid integer, date date, areamunkm double precision, classname character varying(254), ncar_ids integer, car_imovel character varying(2048), continuo integer, velocidade numeric, deltad integer, est_fund character varying(254), dominio character varying(254), tp_dominio character varying(254));


-- View: public.deter_publish_date

-- DROP VIEW public.deter_publish_date;

CREATE OR REPLACE VIEW public.deter_publish_date
 AS
 SELECT remote_data.date
   FROM dblink('hostaddr=<IP or hostname> port=5432 dbname=<DB_NAME> user=postgres password=postgres'::text, 'SELECT date FROM public.deter_publish_date'::text) remote_data(date date);


-- View: public.raw_active_fires

-- DROP VIEW public.raw_active_fires;

CREATE OR REPLACE VIEW public.raw_active_fires
 AS
 SELECT remote_data.id,
    remote_data.view_date,
    remote_data.satelite,
    remote_data.estado,
    remote_data.municipio,
    remote_data.diasemchuva,
    remote_data.precipitacao,
    remote_data.riscofogo,
    remote_data.bioma,
    remote_data.geom
   FROM dblink('hostaddr=<IP or hostname> port=5432 dbname=<DB_NAME> user=postgres password=postgres'::text, 'SELECT id, data as view_date, satelite, estado, municipio, diasemchuva, precipitacao, riscofogo, bioma, geom FROM public.focos_aqua_referencia'::text) remote_data(id integer, view_date date, satelite character varying(254), estado character varying(254), municipio character varying(254), diasemchuva integer, precipitacao double precision, riscofogo double precision, bioma character varying(254), geom geometry(Point,4674));


-- View: public.last_risk_data

-- DROP VIEW public.last_risk_data;

CREATE OR REPLACE VIEW public.last_risk_data
 AS
 SELECT geo.id,
    geo.geom,
    wd.risk,
    (dt.expiration_date - '7 days'::interval)::date AS view_date
   FROM risk.weekly_data wd,
    risk.matrix_ibama_1km geo,
    risk.risk_ibama_date dt
  WHERE wd.date_id = (( SELECT risk_ibama_date.id
           FROM risk.risk_ibama_date
          ORDER BY risk_ibama_date.expiration_date DESC
         LIMIT 1)) AND wd.geom_id = geo.id AND dt.id = wd.date_id;

-- -------------------------------------------------------------------------
-- This session is used for create tables of AMS model
-- -------------------------------------------------------------------------

-- Table: public.spatial_units

-- DROP TABLE IF EXISTS public.spatial_units;

CREATE TABLE IF NOT EXISTS public.spatial_units
(
    id serial NOT NULL,
    dataname character varying NOT NULL,
    as_attribute_name character varying NOT NULL,
    center_lat double precision NOT NULL,
    center_lng double precision NOT NULL,
    description character varying NOT NULL,
    CONSTRAINT spatial_units_pkey PRIMARY KEY (id),
    CONSTRAINT spatial_units_dataname_key UNIQUE (dataname)
)
TABLESPACE pg_default;

-- Table: public.deter_class_group

-- DROP TABLE IF EXISTS public.deter_class_group;

CREATE TABLE IF NOT EXISTS public.deter_class_group
(
    id serial NOT NULL,
    name character varying NOT NULL,
    title character varying NOT NULL,
    orderby integer,
    CONSTRAINT deter_class_group_pkey PRIMARY KEY (id),
    CONSTRAINT deter_class_group_name_key UNIQUE (name)
)
TABLESPACE pg_default;

-- Table: public.deter_class

-- DROP TABLE IF EXISTS public.deter_class;

CREATE TABLE IF NOT EXISTS public.deter_class
(
    id serial NOT NULL,
    name character varying NOT NULL,
    group_id integer,
    CONSTRAINT deter_class_pkey PRIMARY KEY (id),
    CONSTRAINT deter_class_name_key UNIQUE (name),
    CONSTRAINT deter_class_group_id_fkey FOREIGN KEY (group_id)
        REFERENCES public.deter_class_group (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
TABLESPACE pg_default;

-- SCHEMA: deter

-- DROP SCHEMA IF EXISTS deter ;

CREATE SCHEMA IF NOT EXISTS deter AUTHORIZATION postgres;

-- DROP SEQUENCE deter.deter_history_gid_seq;

CREATE SEQUENCE deter.deter_history_gid_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

-- Table: deter.deter_history (The existence of SQL View public.deter_history is mandatory before creating this table)

-- DROP TABLE IF EXISTS deter.deter_history;

CREATE TABLE IF NOT EXISTS deter.deter_history AS
SELECT nextval('deter.deter_history_gid_seq'::regclass) as gid, origin_gid, classname, quadrant, orbitpoint, date, sensor, satellite, areatotalkm,
areamunkm, areauckm, mun, uf, uc, geom, month_year,
NULL::integer as ncar_ids, NULL::text as car_imovel, NULL::integer as continuo, NULL::numeric as velocidade,
NULL::integer as deltad, NULL::character varying(254) as est_fund, NULL::character varying(254) as dominio, 
NULL::character varying(254) as tp_dominio
FROM public.deter_history;

ALTER TABLE deter.deter_history ADD CONSTRAINT deter_history_unique_gid UNIQUE (gid);

CREATE INDEX IF NOT EXISTS index_deter_history_table_geom ON deter.deter_history USING gist(geom);
CREATE INDEX IF NOT EXISTS deter_history_date_idx ON deter.deter_history USING btree (date ASC NULLS LAST);
CREATE INDEX IF NOT EXISTS deter_history_classname_idx ON deter.deter_history USING btree (classname ASC NULLS LAST);

-- Table: deter.deter

-- DROP TABLE IF EXISTS deter.deter;

CREATE TABLE IF NOT EXISTS deter.deter
(
    gid character varying(254) NOT NULL,
    origin_gid integer,
    classname character varying(254),
    quadrant character varying(5),
    orbitpoint character varying(10),
    date date,
    sensor character varying(10),
    satellite character varying(13),
    areatotalkm double precision,
    areamunkm double precision,
    areauckm double precision,
    mun character varying(254),
    uf character varying(2),
    uc character varying(254),
    geom geometry(MultiPolygon,4674),
    month_year character varying(10),
    ncar_ids integer,
    car_imovel text,
    continuo integer,
    velocidade numeric,
    deltad integer,
    est_fund character varying(254),
    dominio character varying(254),
    tp_dominio character varying(254),
    CONSTRAINT deter_pkey PRIMARY KEY (gid)
)
TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS index_deter_table_geom ON deter.deter USING gist(geom);
CREATE INDEX IF NOT EXISTS deter_date_idx ON deter.deter USING btree (date ASC NULLS LAST);
CREATE INDEX IF NOT EXISTS deter_classname_idx ON deter.deter USING btree (classname ASC NULLS LAST);

-- Table: deter.deter_auth

-- DROP TABLE IF EXISTS deter.deter_auth;

CREATE TABLE IF NOT EXISTS deter.deter_auth
(
    gid character varying(254) NOT NULL,
    origin_gid integer,
    classname character varying(254),
    quadrant character varying(5),
    orbitpoint character varying(10),
    date date,
    sensor character varying(10),
    satellite character varying(13),
    areatotalkm double precision,
    areamunkm double precision,
    areauckm double precision,
    mun character varying(254),
    uf character varying(2),
    uc character varying(254),
    geom geometry(MultiPolygon,4674),
    month_year character varying(10),
    ncar_ids integer,
    car_imovel text,
    continuo integer,
    velocidade numeric,
    deltad integer,
    est_fund character varying(254),
    dominio character varying(254),
    tp_dominio character varying(254),
    CONSTRAINT deter_all_pkey PRIMARY KEY (gid)
)
TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS index_deter_auth_table_geom ON deter.deter_auth USING gist(geom);
CREATE INDEX IF NOT EXISTS deter_auth_date_idx ON deter.deter_auth USING btree (date ASC NULLS LAST);
CREATE INDEX IF NOT EXISTS deter_auth_classname_idx ON deter.deter_auth USING btree (classname ASC NULLS LAST);

-- -------------------------------------------------------------------------
-- This session is used for the Active Fires model
-- -------------------------------------------------------------------------

-- SCHEMA: fires

-- DROP SCHEMA IF EXISTS fires ;

CREATE SCHEMA IF NOT EXISTS fires AUTHORIZATION postgres;

-- Table: fires.active_fires

-- DROP TABLE IF EXISTS fires.active_fires;

CREATE TABLE IF NOT EXISTS fires.active_fires
(
    id integer NOT NULL,
    view_date date,
    satelite character varying(254),
    estado character varying(254),
    municipio character varying(254),
    diasemchuva integer,
    precipitacao double precision,
    riscofogo double precision,
    geom geometry(Point,4674),
    CONSTRAINT active_fires_id_pk PRIMARY KEY (id)
)
TABLESPACE pg_default;

-- Index: idx_fires_active_fires_geom

-- DROP INDEX IF EXISTS fires.idx_fires_active_fires_geom;

CREATE INDEX IF NOT EXISTS idx_fires_active_fires_geom
    ON fires.active_fires USING gist
    (geom);

-- DROP INDEX IF EXISTS fires.active_fires_view_date_idx;

CREATE INDEX IF NOT EXISTS active_fires_view_date_idx
    ON fires.active_fires USING btree
    (view_date ASC NULLS LAST);

-- -------------------------------------------------------------------------
-- This session is used for the Risk IBAMA model
-- -------------------------------------------------------------------------

-- SCHEMA: risk

-- DROP SCHEMA IF EXISTS risk ;

CREATE SCHEMA IF NOT EXISTS risk AUTHORIZATION postgres;

-- Table: risk.etl_log_ibama

-- DROP TABLE IF EXISTS risk.etl_log_ibama;

CREATE TABLE IF NOT EXISTS risk.etl_log_ibama
(
    id serial NOT NULL,
    file_name character varying,
    process_status integer,
    process_message character varying,
    last_file_date date NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    CONSTRAINT etl_log_ibama_id_pk PRIMARY KEY (id)
)
TABLESPACE pg_default;

-- Table: risk.risk_ibama_date

-- DROP TABLE IF EXISTS risk.risk_ibama_date;

CREATE TABLE IF NOT EXISTS risk.risk_ibama_date
(
    id serial NOT NULL,
    expiration_date date,
    created_at date NOT NULL DEFAULT now()::date,
    CONSTRAINT risk_ibama_date_id_pk PRIMARY KEY (id)
)
TABLESPACE pg_default;

-- Table: risk.matrix_ibama_1km

-- DROP TABLE IF EXISTS risk.matrix_ibama_1km;

CREATE TABLE IF NOT EXISTS risk.matrix_ibama_1km
(
    id serial NOT NULL,
    geom geometry(Point,4674),
    CONSTRAINT matrix_ibama_1km_id_pk PRIMARY KEY (id)
)
TABLESPACE pg_default;

-- Index: risk_matrix_ibama_1km_geom_idx

-- DROP INDEX IF EXISTS risk.risk_matrix_ibama_1km_geom_idx;

CREATE INDEX IF NOT EXISTS risk_matrix_ibama_1km_geom_idx
    ON risk.matrix_ibama_1km USING gist
    (geom);


-- Table: risk.weekly_data

-- DROP TABLE IF EXISTS risk.weekly_data;

CREATE TABLE IF NOT EXISTS risk.weekly_data
(
    id serial NOT NULL,
    date_id integer,
    geom_id integer,
    risk double precision,
    CONSTRAINT weekly_data_id_pk PRIMARY KEY (id),
    CONSTRAINT weekly_data_date_id_fk FOREIGN KEY (date_id)
        REFERENCES risk.risk_ibama_date (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT weekly_data_geom_id_fk FOREIGN KEY (geom_id)
        REFERENCES risk.matrix_ibama_1km (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)
TABLESPACE pg_default;

-- DROP INDEX IF EXISTS risk.risk_weekly_data_date_idx;

CREATE INDEX IF NOT EXISTS risk_weekly_data_date_idx
    ON risk.weekly_data USING btree
    (date_id ASC NULLS LAST);

-- -------------------------------------------------------------------------
-- This session is used for the Land Use model
-- -------------------------------------------------------------------------

-- Table: public.land_use

-- DROP TABLE IF EXISTS public.land_use;

CREATE TABLE IF NOT EXISTS public.land_use (
	id integer NOT NULL,
	"name" varchar NULL,
	priority integer NULL,
	CONSTRAINT land_use_pk PRIMARY KEY (id)
);
COMMENT ON TABLE public.land_use
  IS 'This table is used to map the land use geotiff pixel values and names used to display in the App.';

-- End of model creation
COMMIT;

-- -------------------------------------------------------------------------
-- This session is used for populate base data on model
-- -------------------------------------------------------------------------
BEGIN;

INSERT INTO public.spatial_units(id, dataname, as_attribute_name, center_lat, center_lng) VALUES (1, 'csAmz_25km', 'id', -5.510617783522636, -58.397927203480116, 'Célula 150x150 km²');
INSERT INTO public.spatial_units(id, dataname, as_attribute_name, center_lat, center_lng) VALUES (2, 'csAmz_150km', 'id', -5.491382969006503, -58.467185764253415, 'Célula 25x25 km²');
INSERT INTO public.spatial_units(id, dataname, as_attribute_name, center_lat, center_lng) VALUES (3, 'csAmz_300km', 'id', -5.491382969006503, -57.792239759933764, 'Célula 300x300 km²');
INSERT INTO public.spatial_units(id, dataname, as_attribute_name, center_lat, center_lng) VALUES (4, 'amz_states', 'nome', -6.384962796500002, -58.97111531179317, 'Estado');
INSERT INTO public.spatial_units(id, dataname, as_attribute_name, center_lat, center_lng) VALUES (5, 'amz_municipalities', 'nome', -6.384962796413522, -58.97111531172743, 'Município');

INSERT INTO public.deter_class_group(id, name) VALUES (1, 'DS', 'DETER Desmatamento', 0);
INSERT INTO public.deter_class_group(id, name) VALUES (2, 'DG', 'DETER Degradação', 1);
INSERT INTO public.deter_class_group(id, name) VALUES (3, 'CS', 'DETER Corte seletivo', 2);
INSERT INTO public.deter_class_group(id, name) VALUES (4, 'MN', 'DETER Mineração', 3);
INSERT INTO public.deter_class_group(id, name) VALUES (5, 'AF', 'Focos (Programa Queimadas)', 4);

INSERT INTO public.deter_class(id, name, group_id) VALUES (1, 'DESMATAMENTO_CR', 1);
INSERT INTO public.deter_class(id, name, group_id) VALUES (2, 'DESMATAMENTO_VEG', 1);
INSERT INTO public.deter_class(id, name, group_id) VALUES (3, 'CICATRIZ_DE_QUEIMADA', 2);
INSERT INTO public.deter_class(id, name, group_id) VALUES (4, 'DEGRADACAO', 2);
INSERT INTO public.deter_class(id, name, group_id) VALUES (5, 'CS_DESORDENADO', 3);
INSERT INTO public.deter_class(id, name, group_id) VALUES (6, 'CS_GEOMETRICO', 3);
INSERT INTO public.deter_class(id, name, group_id) VALUES (7, 'MINERACAO', 4);
INSERT INTO public.deter_class(id, name, group_id) VALUES (8, 'FOCOS', 5);

-- Attention: id values are mapped to "land use" pixel values from the Geotiff file.
INSERT INTO land_use values(1,'APA',3);
INSERT INTO land_use values(2,'Assentamentos',2);
INSERT INTO land_use values(3,'CAR',4);
INSERT INTO land_use values(4,'FPND',5);
INSERT INTO land_use values(5,'TI',0);
INSERT INTO land_use values(6,'UC',1);
INSERT INTO land_use values(12,'Indefinida',6);

-- End of insert metadata
COMMIT;
-- -------------------------------------------------------------------------
-- This session is used for create functions used into GeoServer layers
-- See SQL scripts inside geoserver/sqlviews/ directory
-- -------------------------------------------------------------------------
