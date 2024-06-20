-- DROP old functions

-- DROP FUNCTION IF EXISTS public.get_25km(character varying, date, date, integer[]);
-- DROP FUNCTION IF EXISTS public.get_25km_auth(character varying, date, date, integer[], double precision);
-- DROP FUNCTION IF EXISTS public.get_150km(character varying, date, date, integer[]);
-- DROP FUNCTION IF EXISTS public.get_150km_auth(character varying, date, date, integer[], double precision);
-- DROP FUNCTION IF EXISTS public.get_municipalities(character varying, date, date, integer[]);
-- DROP FUNCTION IF EXISTS public.get_municipalities_auth(character varying, date, date, integer[], double precision);
-- DROP FUNCTION IF EXISTS public.get_states(character varying, date, date, integer[]);
-- DROP FUNCTION IF EXISTS public.get_states_auth(character varying, date, date, integer[], double precision);

-- Create functions with new signature
--
-- -------------------------------------------------------------------------
-- This session is used for create functions used into GeoServer layers
-- -------------------------------------------------------------------------
-- FUNCTION: public.get_25km(character varying, date, date, integer[])

-- DROP FUNCTION IF EXISTS public.get_25km(character varying, date, date, integer[]);

CREATE OR REPLACE FUNCTION public.get_25km(
	clsname character varying,
	startdate date,
	enddate date,
	land_use_ids integer[])
    RETURNS TABLE(suid integer, name character varying, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT su.suid AS suid, su.id AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM public."csAmz_25km" su
LEFT JOIN (
	SELECT rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total, SUM(rii.counts) AS counts
	FROM public."csAmz_25km_land_use" rii
	WHERE (rii.date <= (SELECT a.date FROM deter.deter_publish_date a) OR 'AF'=clsname)
		AND rii.land_use_id = ANY (land_use_ids)
		AND rii.classname = clsname
		AND	rii.date > enddate
		AND	rii.date <= startdate
	GROUP BY rii.suid, rii.classname
) AS ri
ON su.suid = ri.suid;
end;
$BODY$;

ALTER FUNCTION public.get_25km(character varying, date, date, integer[])
    OWNER TO postgres;


-- FUNCTION: public.get_25km_auth(character varying, date, date, integer[], double precision)

-- DROP FUNCTION public.get_25km_auth(character varying, date, date, integer[], double precision);

CREATE OR REPLACE FUNCTION public.get_25km_auth(
	clsname character varying,
	startdate date,
	enddate date,
	land_use_ids integer[],
	risk_threshold double precision)
    RETURNS TABLE(suid integer, name character varying, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT su.suid AS suid, su.id AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM public."csAmz_25km" su
LEFT JOIN (
	SELECT rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total, SUM(rii.counts) AS counts
	FROM public."csAmz_25km_land_use" rii
	WHERE rii.land_use_id = ANY (land_use_ids)
		AND rii.classname = clsname
		AND	rii.date > enddate
		AND	rii.date <= startdate
		AND rii.risk >= risk_threshold
	GROUP BY rii.suid, rii.classname
) AS ri
ON su.suid = ri.suid;
end;
$BODY$;

ALTER FUNCTION public.get_25km_auth(character varying, date, date, integer[], double precision)
    OWNER TO postgres;


-- FUNCTION: public.get_150km(character varying, date, date, integer[])

-- DROP FUNCTION IF EXISTS public.get_150km(character varying, date, date, integer[]);

CREATE OR REPLACE FUNCTION public.get_150km(
	clsname character varying,
	startdate date,
	enddate date,
	land_use_ids integer[])
    RETURNS TABLE(suid integer, name character varying, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT su.suid AS suid, su.id AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM public."csAmz_150km" su
LEFT JOIN (
	SELECT rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total, SUM(rii.counts) AS counts
	FROM public."csAmz_150km_land_use" rii
	WHERE (rii.date <= (SELECT a.date FROM deter.deter_publish_date a) OR 'AF'=clsname)
		AND rii.land_use_id = ANY (land_use_ids)
		AND rii.classname = clsname
		AND	rii.date > enddate
		AND	rii.date <= startdate
	GROUP BY rii.suid, rii.classname
) AS ri
ON su.suid = ri.suid;
end;
$BODY$;

ALTER FUNCTION public.get_150km(character varying, date, date, integer[])
    OWNER TO postgres;

-- FUNCTION: public.get_150km_auth(character varying, date, date, integer[], double precision)

-- DROP FUNCTION IF EXISTS public.get_150km_auth(character varying, date, date, integer[], double precision);

CREATE OR REPLACE FUNCTION public.get_150km_auth(
	clsname character varying,
	startdate date,
	enddate date,
	land_use_ids integer[],
	risk_threshold double precision)
    RETURNS TABLE(suid integer, name character varying, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT su.suid AS suid, su.id AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM public."csAmz_150km" su
LEFT JOIN (
	SELECT rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total, SUM(rii.counts) AS counts
	FROM public."csAmz_150km_land_use" rii
	WHERE rii.land_use_id = ANY (land_use_ids)
		AND rii.classname = clsname
		AND	rii.date > enddate
		AND	rii.date <= startdate
		AND rii.risk >= risk_threshold
	GROUP BY rii.suid, rii.classname
) AS ri
ON su.suid = ri.suid;
end;
$BODY$;

ALTER FUNCTION public.get_150km_auth(character varying, date, date, integer[], double precision)
    OWNER TO postgres;

-- FUNCTION: public.get_municipalities(character varying, date, date, integer[])

-- DROP FUNCTION IF EXISTS public.get_municipalities(character varying, date, date, integer[]);

CREATE OR REPLACE FUNCTION public.get_municipalities(
	clsname character varying,
	startdate date,
	enddate date,
	land_use_ids integer[])
    RETURNS TABLE(suid integer, name character varying, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT su.suid AS suid, su.nome AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM public."amz_municipalities" su
INNER JOIN (
	SELECT rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total , SUM(rii.counts) AS counts
	FROM public."amz_municipalities_land_use" rii
	WHERE (rii.date <= (SELECT a.date FROM deter.deter_publish_date a) OR 'AF'=clsname)
		AND rii.land_use_id = ANY (land_use_ids)
		AND rii.classname = clsname
		AND	rii.date > enddate
		AND	rii.date <= startdate		
	GROUP BY rii.suid, rii.classname
) AS ri
ON su.suid = ri.suid;
end;
$BODY$;

ALTER FUNCTION public.get_municipalities(character varying, date, date, integer[])
    OWNER TO postgres;


-- FUNCTION: public.get_municipalities_auth(character varying, date, date, integer[], double precision)

-- DROP FUNCTION IF EXISTS public.get_municipalities_auth(character varying, date, date, integer[], double precision);

CREATE OR REPLACE FUNCTION public.get_municipalities_auth(
	clsname character varying,
	startdate date,
	enddate date,
	land_use_ids integer[],
	risk_threshold double precision)
    RETURNS TABLE(suid integer, name character varying, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT su.suid AS suid, su.nome AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM public."amz_municipalities" su
INNER JOIN (
	SELECT rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total , SUM(rii.counts) AS counts
	FROM public."amz_municipalities_land_use" rii
	WHERE rii.land_use_id = ANY (land_use_ids)
		AND rii.classname = clsname
		AND	rii.date > enddate
		AND	rii.date <= startdate
		AND rii.risk >= risk_threshold
	GROUP BY rii.suid, rii.classname
) AS ri
ON su.suid = ri.suid;
end;
$BODY$;

ALTER FUNCTION public.get_municipalities_auth(character varying, date, date, integer[], double precision)
    OWNER TO postgres;

-- FUNCTION: public.get_states(character varying, date, date, integer[])

-- DROP FUNCTION IF EXISTS public.get_states(character varying, date, date, integer[]);

CREATE OR REPLACE FUNCTION public.get_states(
	clsname character varying,
	startdate date,
	enddate date,
	land_use_ids integer[])
    RETURNS TABLE(suid integer, name character varying, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT su.suid AS suid, su.nome AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM public."amz_states" su
INNER JOIN (
	SELECT rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total, SUM(rii.counts) AS counts
	FROM public."amz_states_land_use" rii
	WHERE (rii.date <= (SELECT a.date FROM deter.deter_publish_date a) OR 'AF'=clsname)
		AND rii.land_use_id = ANY (land_use_ids)
		AND rii.classname = clsname
		AND	rii.date > enddate
		AND	rii.date <= startdate		
	GROUP BY rii.suid, rii.classname
) AS ri
ON su.suid = ri.suid;
end;
$BODY$;

ALTER FUNCTION public.get_states(character varying, date, date, integer[])
    OWNER TO postgres;


-- FUNCTION: public.get_states_auth(character varying, date, date, integer[], double precision)

-- DROP FUNCTION IF EXISTS public.get_states_auth(character varying, date, date, integer[], double precision);

CREATE OR REPLACE FUNCTION public.get_states_auth(
	clsname character varying,
	startdate date,
	enddate date,
	land_use_ids integer[],
	risk_threshold double precision)
    RETURNS TABLE(suid integer, name character varying, geometry geometry, classname character varying, date date, percentage double precision, area double precision, counts bigint) 
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
    ROWS 1000

AS $BODY$
begin
	return query
SELECT su.suid AS suid, su.nome AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM public."amz_states" su
INNER JOIN (
	SELECT rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total, SUM(rii.counts) AS counts
	FROM public."amz_states_land_use" rii
	WHERE rii.land_use_id = ANY (land_use_ids)
		AND rii.classname = clsname
		AND	rii.date > enddate
		AND	rii.date <= startdate
		AND rii.risk >= risk_threshold
	GROUP BY rii.suid, rii.classname
) AS ri
ON su.suid = ri.suid;
end;
$BODY$;

ALTER FUNCTION public.get_states_auth(character varying, date, date, integer[], double precision)
    OWNER TO postgres;