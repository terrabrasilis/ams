-- name: default - regex
-- classname: DS - \b[A-Z]{2}\b
-- startdate: 2021-01-01 - \d{4}-\d{2}-\d{2}
-- enddate: 2020-12-01 - \d{4}-\d{2}-\d{2}
-- limit: ALL - (ALL|\d+)

SELECT 
	su.suid, su.uf AS state, su.nm_municip AS name, su.geometry, ri.classname, ri.date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS area
FROM 
	public."amz_municipalities" su
LEFT JOIN (
	SELECT 
		suid, classname, MAX(date) AS date, SUM(percentage) AS perc, SUM(area) AS total  
	FROM 
		public."amz_municipalities_risk_indicators" 
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

/*
SELECT p1.suid, p1.id, p1.geometry, p1.classname, p2.date, COALESCE(p2.percentage, 0) - COALESCE(p1.percentage, 0) AS percentage, COALESCE(p2.area, 0) - COALESCE(p1.area, 0) AS area
FROM get_300km_area('%classname%', '%enddate%'::date, '%prevdate%'::date) p1
LEFT OUTER JOIN get_300km_area('%classname%', '%startdate%'::date, '%enddate%'::date) p2
ON p1.suid = p2.suid
ORDER BY
	percentage %order%
LIMIT
	%limit%

*/