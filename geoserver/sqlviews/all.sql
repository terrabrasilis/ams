
-- This is an example used for 150 km cells. Change function names to create other layers

-- used in layer to anonymous user
SELECT p1.suid, p1.name, p1.geometry, COALESCE(p1.classname,p2.classname) as classname, p2.date,
COALESCE(p2.percentage, 0) - COALESCE(p1.percentage, 0) AS percentage,
COALESCE(p2.area, 0) - COALESCE(p1.area, 0) AS area,
COALESCE(p2.counts, 0) - COALESCE(p1.counts, 0) AS counts
FROM get_150km('%classname%', '%enddate%'::date, '%prevdate%'::date) p1
JOIN get_150km('%classname%', '%startdate%'::date, '%enddate%'::date) p2
ON p1.suid = p2.suid
WHERE ('%optype%'='DOWNLOAD' OR (p1.classname IS NOT NULL OR p2.classname IS NOT NULL))
ORDER BY %orderby% %order%
LIMIT %limit%

-- used in layer to authenticated user
SELECT p1.suid, p1.name, p1.geometry, COALESCE(p1.classname,p2.classname) as classname, p2.date,
COALESCE(p2.percentage, 0) - COALESCE(p1.percentage, 0) AS percentage,
COALESCE(p2.area, 0) - COALESCE(p1.area, 0) AS area,
COALESCE(p2.counts, 0) - COALESCE(p1.counts, 0) AS counts
FROM get_150km_auth('%classname%', '%enddate%'::date, '%prevdate%'::date) p1
JOIN get_150km_auth('%classname%', '%startdate%'::date, '%enddate%'::date) p2
ON p1.suid = p2.suid
WHERE ('%optype%'='DOWNLOAD' OR (p1.classname IS NOT NULL OR p2.classname IS NOT NULL))
ORDER BY %orderby% %order%
LIMIT %limit%


-- used in layer to authenticated user
SELECT ri.suid, ri.name, ri.geometry, ri.classname, ri.date as max_date,
COALESCE(ri.percentage, 0) AS percentage,
COALESCE(ri.area, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM get_150km_auth('%classname%', '%startdate%'::date, '%enddate%'::date) ri
WHERE '%optype%'='DOWNLOAD' OR ri.classname IS NOT NULL
ORDER BY %orderby% DESC
LIMIT %limit%

-- used in layer to anonymous user
SELECT ri.suid, ri.name, ri.geometry, ri.classname, ri.date as max_date,
COALESCE(ri.percentage, 0) AS percentage,
COALESCE(ri.area, 0) AS area, COALESCE(ri.counts, 0) AS counts
FROM get_150km('%classname%', '%startdate%'::date, '%enddate%'::date) ri
WHERE '%optype%'='DOWNLOAD' OR ri.classname IS NOT NULL
ORDER BY %orderby% DESC
LIMIT %limit%
