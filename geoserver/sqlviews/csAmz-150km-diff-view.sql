-- name: default - regex
-- classname: DS - \b[A-Z]{2}\b
-- startdate: 2021-01-01 - \d{4}-\d{2}-\d{2}
-- enddate: 2020-12-01 - \d{4}-\d{2}-\d{2}
-- prevdate: 2020-11-01 - \d{4}-\d{2}-\d{2}
-- limit: ALL - (ALL|\d+)
-- order: DESC - (DESC|ASC)
SELECT p1.suid, p1.name, p1.geometry, p1.classname, p2.date, COALESCE(p2.percentage, 0) - COALESCE(p1.percentage, 0) AS percentage, COALESCE(p2.area, 0) - COALESCE(p1.area, 0) AS area
FROM get_150km_area('%classname%', '%enddate%'::date, '%prevdate%'::date) p1
LEFT OUTER JOIN get_150km_area('%classname%', '%startdate%'::date, '%enddate%'::date) p2
ON p1.suid = p2.suid
ORDER BY
	area %order%
LIMIT
	%limit%

/*
SELECT * FROM get_150km_area('DS', '2021-01-01'::date, '2020-12-01'::date)

DROP FUNCTION get_area(character varying,date,date)

SELECT p1.suid, p1.id, p1.geometry, p1.classname, COALESCE(p2.date, p1.date), COALESCE(p2.percentage, 0) - COALESCE(p1.percentage, 0) as percentage, COALESCE(p2.area, 0) - COALESCE(p1.area, 0) AS area
FROM get_150km_area('DS', '2021-01-01'::date, '2020-12-01'::date) p1
LEFT OUTER JOIN get_150km_area('DS', '2021-02-01'::date, '2021-01-01'::date) p2
ON p1.suid = p2.suid
ORDER BY
	area ASC
*/