CREATE SCHEMA IF NOT EXISTS deter;

-- step 1@app.route("/home")
-- def home():
--     return render_template("home.html")
-- @app.route("/<name>")
-- def user(name):
--     return f"Hello-- {name}!"
-- @app.route("/admin")
-- def admin():
--     return redirect(url_for("home")) for authenticated users
TRUNCATE deter.deter_all;

-- step 2 for authenticated users
INSERT INTO deter.deter_all(
    gid, origin_gid, classname, quadrant, orbitpoint, date, date_audit, lot, sensor, satellite,
    areatotalkm, areamunkm, areauckm, mun, uf, uc, geom, month_year, ncar_ids, car_imovel, continuo,
    velocidade, deltad, est_fund, dominio, tp_dominio)
SELECT deter.gid, deter.origin_gid, deter.classname, deter.quadrant, deter.orbitpoint, deter.date,
deter.date_audit, deter.lot, deter.sensor, deter.satellite, deter.areatotalkm,
deter.areamunkm, deter.areauckm, deter.mun, deter.uf, deter.uc, deter.geom, deter.month_year,
0::integer as ncar_ids, ''::text as car_imovel,
0::integer as continuo, 0::numeric as velocidade,
0::integer as deltad, ''::character varying(254) as est_fund,
''::character varying(254) as dominio, ''::character varying(254) as tp_dominio
FROM public.deter_all as deter;

-- step 3 for authenticated users
UPDATE deter.deter_all
SET ncar_ids=ibama.ncar_ids, car_imovel=ibama.car_imovel, velocidade=ibama.velocidade,
deltad=ibama.deltad, est_fund=ibama.est_fund, dominio=ibama.dominio, tp_dominio=ibama.tp_dominio
FROM public.deter_aggregated_ibama as ibama
WHERE deter.deter_all.origin_gid=ibama.origin_gid
AND deter.deter_all.areamunkm=ibama.areamunkm
AND (ibama.ncar_ids IS NOT NULL OR ibama.est_fund IS NOT NULL OR ibama.dominio IS NOT NULL);



-- step 1 for anonymous users
TRUNCATE deter.deter_public;

-- step 2 for anonymous users
INSERT INTO deter.deter_public(
    gid, origin_gid, classname, quadrant, orbitpoint, date, date_audit, lot, sensor, satellite,
    areatotalkm, areamunkm, areauckm, mun, uf, uc, geom, month_year, ncar_ids, car_imovel, continuo,
    velocidade, deltad, est_fund, dominio, tp_dominio)
SELECT deter.gid, deter.origin_gid, deter.classname, deter.quadrant, deter.orbitpoint, deter.date,
deter.date_audit, deter.lot, deter.sensor, deter.satellite, deter.areatotalkm,
deter.areamunkm, deter.areauckm, deter.mun, deter.uf, deter.uc, deter.geom, deter.month_year,
0::integer as ncar_ids, ''::text as car_imovel,
0::integer as continuo, 0::numeric as velocidade,
0::integer as deltad, ''::character varying(254) as est_fund,
''::character varying(254) as dominio, ''::character varying(254) as tp_dominio
FROM public.deter_public as deter;

-- step 3 for anonymous users
UPDATE deter.deter_public
SET ncar_ids=ibama.ncar_ids, car_imovel=ibama.car_imovel, velocidade=ibama.velocidade,
deltad=ibama.deltad, est_fund=ibama.est_fund, dominio=ibama.dominio, tp_dominio=ibama.tp_dominio
FROM public.deter_aggregated_ibama as ibama
WHERE deter.deter_public.origin_gid=ibama.origin_gid
AND deter.deter_public.areamunkm=ibama.areamunkm
AND (ibama.ncar_ids IS NOT NULL OR ibama.est_fund IS NOT NULL OR ibama.dominio IS NOT NULL);



