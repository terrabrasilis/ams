create or replace function get_300km_percentages(clsname varchar, startdate date, enddate date)
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
	public."csAmz_300km" su
LEFT JOIN (
	SELECT 
		rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS total  
	FROM 
		public."csAmz_300km_risk_indicators" rii
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

/*
-73.9909439086914
-16.290519038120973
-41.59353565626206
5.307753100107966
 */