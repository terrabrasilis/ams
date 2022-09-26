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

-- Table: deter.deter_history (The existence of SQL View public.deter_history is mandatory before creating this table)

-- DROP TABLE IF EXISTS deter.deter_history;

CREATE TABLE IF NOT EXISTS deter.deter_history AS
SELECT gid, origin_gid, classname, quadrant, orbitpoint, date, sensor, satellite, areatotalkm,
areamunkm, areauckm, mun, uf, uc, geom, month_year,
NULL::integer as ncar_ids, NULL::text as car_imovel, NULL::integer as continuo, NULL::numeric as velocidade,
NULL::integer as deltad, NULL::character varying(254) as est_fund, NULL::character varying(254) as dominio, 
NULL::character varying(254) as tp_dominio
FROM public.deter_history;

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
    (geom)
    TABLESPACE pg_default;

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
-- -------------------------------------------------------------------------

-- FUNCTION: public.get_25km_area(character varying, date, date)

-- DROP FUNCTION IF EXISTS public.get_25km_area(character varying, date, date);

CREATE OR REPLACE FUNCTION public.get_25km_area(
	clsname character varying,
	startdate date,
	enddate date)
    RETURNS TABLE(suid bigint, name text, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT 
	su.suid AS suid, su.id AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM 
	public."csAmz_25km" su
INNER JOIN (
	SELECT 
		rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total, SUM(rii.counts) AS counts
	FROM 
		public."csAmz_25km_land_use" rii
	WHERE
		rii.classname = clsname
		AND
		rii.date > enddate
		AND
		rii.date <= startdate
	GROUP BY 
	 	rii.suid, rii.classname
) AS ri
ON 
	su.suid = ri.suid;
end;
$BODY$;

-- FUNCTION: public.get_150km_area(character varying, date, date)

-- DROP FUNCTION IF EXISTS public.get_150km_area(character varying, date, date);

CREATE OR REPLACE FUNCTION public.get_150km_area(
	clsname character varying,
	startdate date,
	enddate date)
    RETURNS TABLE(suid bigint, name text, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT 
	su.suid AS suid, su.id AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM 
	public."csAmz_150km" su
INNER JOIN (
	SELECT 
		rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total, SUM(rii.counts) AS counts
	FROM 
		public."csAmz_150km_land_use" rii
	WHERE
		rii.classname = clsname
		AND
		rii.date > enddate
		AND
		rii.date <= startdate
	GROUP BY 
	 	rii.suid, rii.classname
) AS ri
ON 
	su.suid = ri.suid;
end;
$BODY$;

-- FUNCTION: public.get_300km_area(character varying, date, date)

-- DROP FUNCTION IF EXISTS public.get_300km_area(character varying, date, date);

CREATE OR REPLACE FUNCTION public.get_300km_area(
	clsname character varying,
	startdate date,
	enddate date)
    RETURNS TABLE(suid bigint, name text, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT 
	su.suid AS suid, su.id AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM 
	public."csAmz_300km" su
INNER JOIN (
	SELECT 
		rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total, SUM(rii.counts) AS counts
	FROM 
		public."csAmz_300km_land_use" rii
	WHERE
		rii.classname = clsname
		AND
		rii.date > enddate
		AND
		rii.date <= startdate
	GROUP BY 
	 	rii.suid, rii.classname
) AS ri
ON 
	su.suid = ri.suid;
end;
$BODY$;

-- FUNCTION: public.get_municipalities_area(character varying, date, date)

-- DROP FUNCTION IF EXISTS public.get_municipalities_area(character varying, date, date);

CREATE OR REPLACE FUNCTION public.get_municipalities_area(
	clsname character varying,
	startdate date,
	enddate date)
    RETURNS TABLE(suid bigint, state text, name text, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT
	su.suid AS suid, su.uf AS state, su.nome AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM 
	public."amz_municipalities" su
INNER JOIN (
	SELECT 
		rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total , SUM(rii.counts) AS counts
	FROM 
		public."amz_municipalities_land_use" rii
	WHERE
		rii.classname = clsname
		AND
		rii.date > enddate
		AND
		rii.date <= startdate		
	GROUP BY 
	 	rii.suid, rii.classname
) AS ri
ON 
	su.suid = ri.suid;
end;
$BODY$;

-- FUNCTION: public.get_states_area(character varying, date, date)

-- DROP FUNCTION IF EXISTS public.get_states_area(character varying, date, date);

CREATE OR REPLACE FUNCTION public.get_states_area(
	clsname character varying,
	startdate date,
	enddate date)
    RETURNS TABLE(suid bigint, name text, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT 
	su.suid AS suid, su.nome AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM 
	public."amz_states" su
INNER JOIN (
	SELECT 
		rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total, SUM(rii.counts) AS counts
	FROM 
		public."amz_states_land_use" rii
	WHERE
		rii.classname = clsname
		AND
		rii.date > enddate
		AND
		rii.date <= startdate		
	GROUP BY 
	 	rii.suid, rii.classname
) AS ri
ON 
	su.suid = ri.suid;
end;
$BODY$;