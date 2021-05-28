DROP FUNCTION get_states_percentages(character varying,date,date);

create or replace function get_states_percentages(clsname varchar, startdate date, enddate date)
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
	su.suid AS suid, su."NM_ESTADO" AS id, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.total, 0) AS percentage
FROM 
	public."amz_states" su
LEFT JOIN (
	SELECT 
		rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS total  
	FROM 
		public."amz_states_risk_indicators" rii
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
