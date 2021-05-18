DROP FUNCTION get_municipalities_percentages(character varying,date,date);

create or replace function get_municipalities_percentages(clsname varchar, startdate date, enddate date)
	returns table (
			suid bigint,
			id text,
			geometry geometry(MultiPolygon,4326),
			classname varchar,
			date date,
			percentage double precision
	)
	language plpgsql
as $$
begin
	return query
SELECT 
	su.suid AS suid, su.nm_municip AS id, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.total, 0) AS percentage
FROM 
	public."amz_municipalities" su
LEFT JOIN (
	SELECT 
		rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS total  
	FROM 
		public."amz_municipalities_risk_indicators" rii
	GROUP BY 
	 	rii.suid, rii.classname
) AS ri
ON 
	su.suid = ri.suid 
	AND 
	ri.classname = clsname
	AND
	ri.date > enddate
	AND
	ri.date <= startdate;
end;$$


-- name: default - regex
-- classname: DS - \b[A-Z]{2}\b
-- startdate: 2021-01-01 - \d{4}-\d{2}-\d{2}
-- enddate: 2020-12-01 - \d{4}-\d{2}-\d{2}
-- prevdate: 2020-11-01 - \d{4}-\d{2}-\d{2}
-- limit: ALL - (ALL|\d+)
-- order: DESC - (DESC|ASC)
SELECT p1.suid, p1.id, p1.geometry, p1.classname, p2.date, COALESCE(p2.percentage, 0) - COALESCE(p1.percentage, 0) AS percentage
FROM get_municipalities_percentages('%classname%', '%enddate%'::date, '%prevdate%'::date) p1
LEFT OUTER JOIN get_municipalities_percentages('%classname%', '%startdate%'::date, '%enddate%'::date) p2
ON p1.suid = p2.suid
ORDER BY 
	percentage %order%
LIMIT 
	%limit%	
