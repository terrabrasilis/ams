    DROP FUNCTION get_municipalities_area(character varying,date,date);

    create or replace function get_municipalities_area(clsname varchar, startdate date, enddate date)
        returns table (
                suid bigint,
                name text,
                geometry geometry(MultiPolygon,4326),
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
        su.suid AS suid, su.nm_municip AS name, su.geometry AS geometry, ri.classname AS classname, ri.date AS date, COALESCE(ri.perc, 0) AS percentage, COALESCE(ri.total, 0) AS percentage
    FROM
        public."amz_municipalities" su
    LEFT JOIN (
        SELECT
            rii.suid, rii.classname, MAX(rii.date) AS date, SUM(rii.percentage) AS perc, SUM(rii.area) AS total
        FROM
            public."amz_municipalities_risk_indicators" rii
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
