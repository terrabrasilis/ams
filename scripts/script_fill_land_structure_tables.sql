drop table if exists amz_states_class;

create table amz_states_class as
select suid,date,class_id,sum(num_pixels) from amz_states a 
inner join deter.deter_all b
on st_intersects(st_transform(a.geometry,4674), b.geom)
inner join deter_land_structure c
on b.gid = c.deter_gid 
group by suid,date,suid,class_id;

drop table if exists "csAmz_150km_class";
create table "csAmz_150km_class" as 
select suid,date,class_id,sum(num_pixels) as pixels from "csAmz_150km" a 
inner join deter.deter_all b
on st_intersects(st_transform(a.geometry,4674), b.geom)
inner join deter_land_structure c
on b.gid = c.deter_gid 
group by suid,date,class_id;
drop table if exists "csAmz_300km_class";
create table "csAmz_300km_class" as 
select suid,date,class_id,sum(num_pixels) as pixels from "csAmz_300km" a 
inner join deter.deter_all b
on st_intersects(st_transform(a.geometry,4674), b.geom)
inner join deter_land_structure c
on b.gid = c.deter_gid 
group by suid,date,class_id;
drop table if exists amz_municipalities_land_use;
create table amz_municipalities_land_use as
select suid,date,class_id,sum(num_pixels) as pixels from amz_municipalities a
inner join deter.deter_all b
on st_intersects(st_transform(a.geometry,4674), b.geom)
inner join deter_land_structure c
on b.gid = c.deter_gid
group by suid,date,class_id;