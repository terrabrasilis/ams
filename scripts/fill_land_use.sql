drop table if exists land_use;
CREATE TABLE public.land_use (
	id serial2 NOT NULL,
	"name" varchar NULL,
	CONSTRAINT land_use_pk PRIMARY KEY (id)
);
INSERT INTO land_use values(1,'APA');
INSERT INTO land_use values(2,'Assentamentos');
INSERT INTO land_use values(3,'CAR');
INSERT INTO land_use values(4,'FPND');
INSERT INTO land_use values(5,'TI');
INSERT INTO land_use values(6,'UC');
INSERT INTO land_use values(12,'Indefinida');
