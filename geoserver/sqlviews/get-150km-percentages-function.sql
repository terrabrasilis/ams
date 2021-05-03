
create or replace function get_150km_percentages(clsname varchar, startdate date, enddate date)
	returns table (
			suid bigint,
			id text,
			geometry geometry(Polygon,4326),
			classname varchar,
			date date,
			percentage double precision
	)
	language plpgsql
as $$
begin
	return query
SELECT 
	su.suid AS suid, su.id AS id, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.total, 0) AS percentage
FROM 
	public."csAmz_150km" su
LEFT JOIN (
	SELECT 
		rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS total  
	FROM 
		public."csAmz_150km_risk_indicators" rii
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
FROM get_150km_percentages('%classname%', '%enddate%'::date, '%prevdate%'::date) p1
LEFT OUTER JOIN get_150km_percentages('%classname%', '%startdate%'::date, '%enddate%'::date) p2
ON p1.suid = p2.suid
ORDER BY 
	percentage %order%
LIMIT 
	%limit%	

SELECT * FROM get_150km_percentages('DS', '2021-01-01'::date, '2020-12-01'::date)

DROP FUNCTION get_percentages(character varying,date,date)

SELECT p1.suid, p1.id, p1.geometry, p1.classname, COALESCE(p2.date, p1.date), COALESCE(p2.percentage, 0) - COALESCE(p1.percentage, 0) AS percentage
FROM get_percentages('DS', '2021-01-01'::date, '2020-12-01'::date, 200) p1
LEFT OUTER JOIN get_percentages('DS', '2021-02-01'::date, '2021-01-01'::date, 200) p2
ON p1.suid = p2.suid
ORDER BY 
	percentage DESC	

-73.99094386360547
16.290519038120973
42.94342766490137
5.307753100107966