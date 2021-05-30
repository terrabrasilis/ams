DROP FUNCTION get_300km_area(character varying,date,date);

create or replace function get_300km_area(clsname varchar, startdate date, enddate date)
	returns table (
			suid bigint,
			name text,
			geometry geometry(Polygon,4326),
			classname varchar,
			date date,
			percentage double precision,
			area double precision
	)
	language plpgsql
as $$
begin
	return query
SELECT 
	su.suid AS suid, su.id AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area
FROM 
	public."csAmz_300km" su
LEFT JOIN (
	SELECT 
		rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total  
	FROM 
		public."csAmz_300km_risk_indicators" rii
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
end;$$
