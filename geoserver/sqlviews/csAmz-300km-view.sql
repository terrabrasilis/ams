-- name: default - regex
-- classname: DS - \b[A-Z]{2}\b
-- startdate: 2021-01-01 - \d{4}-\d{2}-\d{2}
-- enddate: 2020-12-01 - \d{4}-\d{2}-\d{2}
-- limit: ALL - (ALL|\d+)

SELECT 
	su.suid, su.id AS name, su.geometry, ri.classname, ri.date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area
FROM 
	public."csAmz_300km" su
LEFT JOIN (
	SELECT 
		suid, classname, MAX(date) AS date, SUM(percentage) AS perc, SUM(area) AS total  
	FROM 
		public."csAmz_300km_risk_indicators" 
	WHERE
		classname = '%classname%' 
		AND
		date > '%enddate%'::date
		AND
		date <= '%startdate%'::date		
	GROUP BY 
	 	suid, classname
) AS ri
ON 
	su.suid = ri.suid
ORDER BY 
	area DESC
LIMIT
	%limit%
