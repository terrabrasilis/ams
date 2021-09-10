create view deter_aggregated_ibama
as
SELECT *
   FROM   dblink('hostaddr=127.0.0.1 port=5432 dbname=deter_aggregated_ibama user=postgres password=postgres','SELECT * FROM deter_aggregated_ibama_tb')
   as deter_aggregated_ibama(	origin_gid int4,
	"date" date,
	areamunkm float8,
	classname varchar(254),
	ncar_ids int4,
	car_imovel varchar(2048),
	continuo int4,
	velocidade numeric,
	deltad int4,
	est_fund varchar(254),
	dominio varchar(254),
	tp_dominio varchar(254)
);


create view deter_public
as
SELECT *
   FROM   dblink('hostaddr=127.0.0.1 port=5432 dbname=deter_public user=postgres password=postgres','SELECT * FROM deter_public_tb')
   as deter_apublic(	gid text,
	origin_gid int4,
	classname varchar(254),
	quadrant varchar(5),
	orbitpoint varchar(10),
	"date" date,
	date_audit date,
	lot varchar(254),
	sensor varchar(10),
	satellite varchar(13),
	areatotalkm float8,
	areamunkm float8,
	areauckm float8,
	mun varchar(254),
	uf varchar(2),
	uc varchar(254),
	geom geometry(multipolygon, 4674),
	month_year varchar(10)
);


create view deter_all
as
SELECT *
   FROM   dblink('hostaddr=127.0.0.1 port=5432 dbname=deter_all user=postgres password=postgres','SELECT * FROM deter_all_tb')
   as deter_all(	gid text,
	origin_gid int4,
	classname varchar(254),
	quadrant varchar(5),
	orbitpoint varchar(10),
	"date" date,
	date_audit date,
	lot varchar(254),
	sensor varchar(10),
	satellite varchar(13),
	areatotalkm float8,
	areamunkm float8,
	areauckm float8,
	mun varchar(254),
	uf varchar(2),
	uc varchar(254),
	geom geometry(multipolygon, 4674),
	month_year varchar(10)
);


