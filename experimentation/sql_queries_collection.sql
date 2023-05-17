------------------------------------------------------------------------------------------------------------------------
-- This code is a collection of queries used to test the point cloud generation sql queries
-- and to analyze and visualize results
------------------------------------------------------------------------------------------------------------------------

-- create simplified england boundary table
create table england_boundary as
	select
		st_buffer(st_simplify(cb.geom, 500), 0.0) geom
	from country_boundaries cb
	where cb.ctry21nm='England'


create index england_boundary_geom_geom_idx on england_boundary using gist(geom);

select count(gid)
from footprint_ids_in_england

-- create table with footprint ids in england to save query time
create table footprint_ids_in_england as
select fv.gid, fv.unique_property_number upn
from footprints_verisk fv, england_boundary eb
where st_intersects(eb.geom, fv.geom)


-- analysis of number of EPC per footprint in dataset
with footprints_in_dataset as (
	select fid.id_fp, fid.num_p_in_pc, fv.unique_property_number upn
	from footprint_ids_in_data_set_uprn_verisk fid
	left join footprints_verisk fv on fid.id_fp=fv.gid
	where fid.num_p_in_pc notnull
),
footprints as (
	select fp.id_fp, vul.uprn uprn
	from footprints_in_dataset fp
	left join verisk_uprn_link vul on fp.upn=vul.upn
),
fp_w_epc as (
	select fp.id_fp, fp.uprn, ea."LMK_KEY" epc_id
	from footprints fp
	left join epc_reduced_all ea on fp.uprn=ea."UPRN"
),
analysis as (
	select count(epc_id) count_epc
	from fp_w_epc
	group by id_fp
),
threshold as (
	select 10 val
),
lower_than_threshold as (
	select count_epc, count(count_epc)
	from analysis , threshold
	where count_epc<threshold.val
	group by count_epc
	order by count_epc asc
),
higher_than_threshold as (
	select count(count_epc) num_higher_than_threshold
	from analysis , threshold
	where count_epc>=threshold.val
)
select *
from lower_than_threshold, higher_than_threshold


-- analysis of number of UPRN per footprint in dataset
with footprints_in_dataset as (
	select fid.id_fp, fid.num_p_in_pc, fv.unique_property_number upn
	from footprint_ids_in_data_set_uprn_verisk fid
	left join footprints_verisk fv on fid.id_fp=fv.gid
	where fid.num_p_in_pc notnull
),
footprints as (
	select fp.id_fp, vul.uprn uprn
	from footprints_in_dataset fp
	left join verisk_uprn_link vul on fp.upn=vul.upn
),
analysis as (
	select count(uprn) count_uprn
	from footprints
	group by id_fp
),
threshold as (
	select 10 val
),
lower_than_threshold as (
	select count_uprn, count(count_uprn)
	from analysis , threshold
	where count_uprn<threshold.val
	group by count_uprn
	order by count_uprn asc
),
higher_than_threshold as (
	select count(count_uprn) num_higher_than_threshold
	from analysis , threshold
	where count_uprn>=threshold.val
)
select *
from lower_than_threshold, higher_than_threshold

-- analysis of number of UPRN per footprint in england
with footprints_in_england as (
	select fiie.upn, fiie.gid id_fp
	from footprint_ids_in_england fiie
),
footprints as (
	select fp.id_fp, vul.uprn uprn
	from footprints_in_england fp
	left join verisk_uprn_link vul on fp.upn=vul.upn
),
analysis as (
	select count(uprn) count_uprn
	from footprints
	group by id_fp
),
threshold as (
	select 10 val
),
lower_than_threshold as (
	select count_uprn, count(count_uprn)
	from analysis , threshold
	where count_uprn<threshold.val
	group by count_uprn
	order by count_uprn asc
),
higher_than_threshold as (
	select count(count_uprn) num_higher_than_threshold
	from analysis , threshold
	where count_uprn>=threshold.val
)
select *
from lower_than_threshold, higher_than_threshold

-- analysis of number of EPC per footprint in england
with footprints_in_england as (
	select fiie.upn, fiie.gid id_fp
	from footprint_ids_in_england fiie
),
footprints as (
	select fp.id_fp, vul.uprn uprn
	from footprints_in_england fp
	left join verisk_uprn_link vul on fp.upn=vul.upn
),
fp_w_epc as (
	select fp.id_fp, fp.uprn, ea."LMK_KEY" epc_id
	from footprints fp
	left join epc_reduced_all ea on fp.uprn=ea."UPRN"
),
analysis as (
	select count(epc_id) count_epc
	from fp_w_epc
	group by id_fp
),
threshold as (
	select 10 val
),
lower_than_threshold as (
	select count_epc, count(count_epc)
	from analysis , threshold
	where count_epc<threshold.val
	group by count_epc
	order by count_epc asc
),
higher_than_threshold as (
	select count(count_epc) num_higher_than_threshold
	from analysis , threshold
	where count_epc>=threshold.val
)
select *
from lower_than_threshold, higher_than_threshold



-- query to create final result with verisk uprn (instead of geographic intersection uprn)
with footprints as (
	select
		ftp.id_fp,
		ftp.pc_file_name,
		ftp.num_p_in_pc,
		vul.uprn,
		fv.geom
	from fp_to_pc ftp
	left join footprints_verisk fv on ftp.id_fp=fv.gid
	left join verisk_uprn_link vul on fv.unique_property_number=vul.upn
)
select *
from footprints fp
left join epc_all e on fp.uprn=e."UPRN"


select count(distinct fp.id_fp)
from footprints fp
left join epc_all e on fp.uprn=e."UPRN"
where e."LMK_KEY" notnull


-- visualize uprn and verisk footprints
select
	fv.unique_property_number upn,
	vul.uprn,
	st_transform(fv.geom, 4326),
	st_transform(u.geom, 4326) geom_uprn
from footprints_verisk fv
left join verisk_uprn_link vul on fv.unique_property_number=vul.upn
left join uprn u on u.uprn=vul.uprn
limit 1000


-- check if verisk footprints uprn information aligns with
-- geometry intersection uprn link (of footprints in dataset)
with fp_id_ubn as (
	select
		fiidsu.id_fp,
		fiidsu.uprn,
		fv.unique_property_number upn,
		fv.geom
	from footprint_ids_in_data_set_uprn fiidsu
	left join footprints_verisk fv on fiidsu.id_fp=fv.gid
	limit 100
),
fp_uprn as (
	select
		fp.id_fp,
		fp.uprn,
		fp.upn,
		fp.geom,
		u.geom geom_uprn
	from fp_id_ubn fp
	left join uprn u on u.uprn=fp.uprn
)
select
	fp.id_fp,
	fp.uprn,
	fp.upn,
	vul.uprn verisk_uprn,
	vul.upn,
	fp.geom geom_fp,
	fp.geom_uprn
from fp_uprn fp
left join verisk_uprn_link vul on fp.upn=vul.upn
limit 100


-- select all footprints within bounding boxes
with bbox as (
	select 'POLYGON ((-1.083835927313378 53.95357692232674, -1.083835927313378 53.95495794790006, -1.0861105526756154 53.95495794790006, -1.0861105526756154 53.95357692232674, -1.083835927313378 53.95357692232674))'::geometry
	--select 'POLYGON ((-1.0623086232467667 53.93276314164747, -1.0623086232467667 53.93522328398231, -1.0675532238619023 53.93522328398231, -1.0675532238619023 53.93276314164747, -1.0623086232467667 53.93276314164747))'::geometry
)
select *, st_transform(geom_fp, 4326)
from bbox, "E06000014" fv
where st_intersects(fv.geom_fp, st_transform(st_setsrid(bbox.geometry, 4326), 27700))


-- select points in bounding box
with bbox as (
	select st_transform(st_setsrid('POLYGON ((-1.0623086232467667 53.93276314164747, -1.0623086232467667 53.93522328398231, -1.0675532238619023 53.93522328398231, -1.0675532238619023 53.93276314164747, -1.0623086232467667 53.93276314164747))'::geometry, 4326), 27700))
),
patch_unions_in_bbox as (
	select pc_union(pc_intersection(pa, bbox.geometry)) pau
	from bbox, uk_lidar_data uld
	where pc_intersects(uld.pa, bbox.geometry)
),
bbox_pc as (
    select
        st_union(geom) geom_pc,
        pc_get(p, 'X') x,
        pc_get(p, 'Y') y,
        pc_get(p, 'Z') z,
        st_makepoint(pc_get(p, 'X'), pc_get(p, 'Y')) geom_p,
    from (
        select pc_explode(pau) p, pc_explode(pau)::geometry geom
            from patch_unions_in_bbox
        ) po
)
select
from bbox_pc


-- visualize output area geoms in AOI
with boundary as (
	select *
	from local_authority_boundaries lab
	where lab.lad21cd='E06000014'
)
select
	*,
	st_transform(lab.geom, 4326) labgeom,
	st_transform(oab.geom, 4326) labgeom
from boundary lab
left join output_area_boundaries oab on st_intersects(lab.geom, oab.geom)

-- visualize AIO boundaries
select
	lab.lad21cd,
	lad21nm,
	st_transform(st_simplify(lab.geom, 300),4326)
from local_authority_boundaries lab
where
	lab.lad21cd='E06000014' or
	lab.lad21cd='E06000026' or
	lab.lad21cd='E06000031' or
	lab.lad21cd='E07000148' or
	lab.lad21cd='E07000178' or
	lab.lad21cd='E08000012' or
	lab.lad21cd='E08000026' or
	lab.lad21cd='E09000033' or
	lab.lad21cd='' or
	lab.lad21cd='E07000227' or
	lab.lad21cd='E07000142' or
	lab.lad21cd='E07000012' or
	lab.lad21cd='E07000036' or
	lab.lad21cd='E07000040' or
	lab.lad21cd='E08000030' or
	lab.lad21cd='E07000030' or
	lab.lad21cd='E09000029'



-- classification into rural urban classes (f1-a2) for AOIs
with lads as (
	select distinct lab.lad21cd
	from local_authority_boundaries lab
),
f1 as (
select lad21cd, sum(num_fp) f1_sum
from ruoa_classification_aoi rca where code='F1'
group by lad21cd, classification_10, code
),
f2 as (
select lad21cd, sum(num_fp) f2_sum
from ruoa_classification_aoi rca where code='F2'
group by lad21cd, classification_10, code
),
d1 as (
select lad21cd,	sum(num_fp) d1_sum
from ruoa_classification_aoi rca where code='D1'
group by lad21cd, classification_10, code
),
d2 as (
select lad21cd,	sum(num_fp) d2_sum
from ruoa_classification_aoi rca where code='D2'
group by lad21cd, classification_10, code
),
e1 as (
select lad21cd,	sum(num_fp) e1_sum
from ruoa_classification_aoi rca where code='E1'
group by lad21cd, classification_10, code
),
e2 as (
select lad21cd,	sum(num_fp) e2_sum
from ruoa_classification_aoi rca where code='E2'
group by lad21cd, classification_10, code
),
c1 as (
select lad21cd,	sum(num_fp) c1_sum
from ruoa_classification_aoi rca where code='C1'
group by lad21cd, classification_10, code
),
c2 as (
select lad21cd,	sum(num_fp) c2_sum
from ruoa_classification_aoi rca where code='C2'
group by lad21cd, classification_10, code
),
a1 as (
select lad21cd,	sum(num_fp) a1_sum
from ruoa_classification_aoi rca where code='A1'
group by lad21cd, classification_10, code
),
a2 as (
select lad21cd,	sum(num_fp) a2_sum
from ruoa_classification_aoi rca where code='A2'
group by lad21cd, classification_10, code
)
select
	lads.lad21cd
	f1_sum,
	f2_sum,
	d1_sum,
	d2_sum,
	e1_sum,
	e2_sum,
	c1_sum,
	c2_sum,
	a1_sum,
	a2_sum
from f1
left join f2 on lads.lad21cd=f2.lad21cd
left join d1 on lads.lad21cd=d1.lad21cd
left join d2 on lads.lad21cd=d2.lad21cd
left join e1 on lads.lad21cd=e1.lad21cd
left join e2 on lads.lad21cd=e2.lad21cd
left join c1 on lads.lad21cd=c1.lad21cd
left join c2 on lads.lad21cd=c2.lad21cd
left join a1 on lads.lad21cd=a1.lad21cd
left join a2 on lads.lad21cd=a2.lad21cd

-- rural urban of AOI
create materialized view ruoa_classification_aoi as
	with oa_to_lad as (
		select
			oab.oa11cd,
			lab.lad21cd
		from output_area_boundaries oab
		left join local_authority_boundaries lab on st_intersects(lab.geom, oab.geom)
	),
	lad_classification as (
		select *
		from ruoa_classification rc
		left join oa_to_lad otl on otl.oa11cd=rc.oaid
	)
	select *
	from lad_classification

-- materialized view of footprints - authority district and output area link
create materialized view footprints_to_lad_to_oab as
select
	fv.gid id_fp,
	lab.lad21cd id_lad,
	oab.oa11cd id_oab
from footprints_verisk fv
left join local_authority_boundaries lab on st_intersects(fv.geom, lab.geom)
left join output_area_boundaries oab on st_intersects(fv.geom, oab.geom)


-- rural urban of england
select classification_10 , count(classification_10), sum(num_fp), code
from ruoa_classification rc
group by rc.classification_10, code

-- rural urban of footprints in dataset
with footprint_codes_distinct as (
	select distinct id_fp, code, oaid_code
	from ruoa_classification_fps_in_dataset rcfid
)
select code, oaid_code, count(*)
from footprint_codes_distinct
group by code, oaid_code

-- analyse how many footprints are duplicated and have different code: 203
with footprint_codes_distinct as (
	select distinct id_fp, code
	from ruoa_classification_fps_in_dataset rcfid
)
select count(*)
from footprint_codes_distinct

select count(*)
from footprint_ids_in_data_set fiids


-- rural urban analysis grouped by output area (faster than by footprints)
create materialized view ruoa_classification as
	with oa_count as (
		select
			ruoa.oaid oaid,
			ruoa.classification_10,
			count(ruoa.gid) num_fp
		from rural_urban_output_area ruoa
		left join footprints_verisk fv on st_intersects(ruoa.geom, fv.geom)
		group by ruoa.oaid, ruoa.classification_10
	)
	select
		ruc."Output Area 2011 Code" oaid,
		ruc."Rural Urban Classification 2011 code" code,
		ruc."Rural Urban Classification 2011 (10 fold)" classification_10,
		ruc."Rural Urban Classification 2011 (2 fold)" classification_2,
		oac.num_fp
	from output_area_rural_urban_classification ruc
	left join oa_count oac on oac.oaid=ruc."Output Area 2011 Code"

-- rural urban analysis grouped by footprints
create materialized view ruoa_classification_fps_in_dataset as
	with footprints as (
		select
		    fv.gid id_fp,
	        fv.geom geom
	    from footprint_ids_in_data_set fiids
	    left join footprints_verisk fv on fiids.id_fp=fv.gid
	),
	footprints_lad as (
	    select
	        fp.id_fp id_fp,
	        lab.lad21cd lad,
	        fp.geom geom
	    from footprints fp
	    left join local_authority_boundaries lab on st_intersects(fp.geom, lab.geom)
	),
	footprints_rural_urban as (
	    select
	        fp.id_fp id_fp,
	        fp.lad lad,
	        ruoa.oaid oaid,
	        ruoa.classification_code oaid_code,
	        ruoa.classification_10 code
	    from footprints_lad fp
	    left join rural_urban_output_area ruoa on st_intersects(fp.geom, ruoa.geom)
	)
	select *
	from footprints_rural_urban



-- check if EPC are in AOI
select e."LMK_KEY", e."UPRN" uprn, st_transform(u.geom, 4326)
from uprn u
left join epc e on e."UPRN"=u.uprn
where e."LMK_KEY" notnull

-- analyze discrete value of table column
with footprints_dataset as (
	select *
	from footprint_ids_in_data_set fiids
	left join footprints_verisk fv on fiids.id_fp=fv.gid
),

with analytics_attributes as (
	select fp.use attr -- select column
	from footprints_verisk fp -- select table
)
select attr, count(attr)
from analytics_attributes
group by attr


-- analyse continous value of table column
with footprints_dataset as (
	select *
	from footprint_ids_in_data_set fiids
	left join footprints_verisk fv on fiids.id_fp=fv.gid
),
with histogram as (
   -- select width_bucket(fv.height, min, max, 19) as bucket,
		select width_bucket(fv.property_area  , 0, 200, 9) as bucket,
          -- int4range(min(fv.height)::INTEGER, max(fv.height)::INTEGER, '[]') as range,
		  int4range(min(fv.property_area)::INTEGER, min(fv.property_area)::INTEGER, '[]') as range,
          count(*) as freq
     from footprints_verisk fv
 group by bucket
 order by bucket
)
 select bucket, range, freq,
        repeat('■',
               (   freq::float
                 / max(freq) over()
                 * 30
               )::int
        ) as bar
   from histogram;


select width_bucket(fv.height, 0, 50, 20) as buckets,
		count(*)
	from footprints_verisk fv
group by buckets
order by buckets;

-- age distribution all footprints
with fps as (
	select *
	from footprints_verisk fv
)
select fps.age, count(*)
from fps
group by fps.age


-- Count footprints in boundary
with boundary as (
	select lab.geom
	from local_authority_boundaries lab
	where lab.lad21cd='E07000030'
)
select count(*)
from footprints_verisk fv, boundary b
where st_intersects(fv.geom, b.geom)


-- produce a data lice materialized view of LAD boundary with simplified boundary geometry
create materialized view "E08000012" as (
	select gid, st_simplify(labc.geom, 300) geom, lad21nm
	from local_authority_boundaries labc
	where labc.lad21cd='E08000012'
)


-- analyze oxford results
select id_fp, num_p_in_pc, geom, st_transform(geom_fp, 4326)
from oxford_results or2
where geom is not null and num_p_in_pc > 50
group by id_fp, num_p_in_pc, geom, geom_fp
order by num_p_in_pc asc

-- analyze potentiall overlapping lidar tiles
with env_2019 as (
	select st_envelope(st_union(pc_envelopegeometry(ukl2019.pa))) geom
	from uk_lidar_data_2019 ukl2019
	limit 200
),
env_2021 as (
	select st_envelope(st_union(pc_envelopegeometry(ukl2021.pa))) geom
	from uk_lidar_data_2021 ukl2021
	limit 200
),
p_2019 as (
	select pc_explode(pa)::geometry geom_pc
	from uk_lidar_data_2019 ukl2019
	limit 200
),
p_19in21 as (
	select *
	from p_2019, env_2021
	where st_intersects(p_2019.geom_pc, env_2021.geom)
),
p_2021 as (
	select pc_explode(pa)::geometry geom_pc
	from uk_lidar_data_2021 ukl2021
	limit 200
),
d_p_2021 as (
	select distinct p_2021.geom_pc geom2021
	from p_2021
),
d_p_2019 as (
	select distinct p_2019.geom_pc geom2019
	from p_2019, p_2021
)
select *
from p_2019, p_2021

-- visualize overlapping point cloud envelopes
with env_2019 as (
	select pc_envelopegeometry(ukl2019.pa) geom
	from uk_lidar_data_2019 ukl2019
),
env_2021 as (
	select pc_envelopegeometry(ukl2021.pa) geom
	from uk_lidar_data_2021 ukl2021
)
select
  st_transform(a.geom, 4326),
  st_transform(b.geom, 4326)
FROM (
  SELECT geom, ROW_NUMBER() OVER (ORDER BY geom) AS rn
  FROM env_2019
) a
FULL JOIN (
  SELECT geom, ROW_NUMBER() OVER (ORDER BY geom) AS rn
  FROM env_2021
) b
ON a.rn = b.rn


-- inspect pointcloud data in boundary
with boundary as (
	select lab.geom
	from local_authority_boundaries lab
	where lab.lad21cd='E08000026'
)
select st_transform(st_envelope(st_union(pc_envelopegeometry(uld.pa))), 4326) geom
from uk_lidar_data uld


-- footprints in AOI materialized view
create materialized view "E06000014" as (
	with area_of_interest as (
	    select st_transform(geom, 27700) geom
	    from local_authority_boundaries lab
	    where lab.lad21cd = 'E06000014'
	),
	footprints as (
	    select row_number() over (order by fps.gid) as id_fp_chunks, fps.geom geom_fp, fps.gid id_fp
	    from footprints_verisk fps, area_of_interest
	    where st_intersects(fps.geom, area_of_interest.geom)
	    limit 1000000000
	)
	select *
	from footprints
)


	with area_of_interest as (
	    select st_transform(geom, 27700) geom
	    from local_authority_boundaries lab
	    where lab.lad21cd = 'E07000178'
	),
	footprints as (
	    select row_number() over (order by fps.gid) as id_fp_chunks, fps.geom geom_fp, fps.gid id_fp
	    from footprints_verisk fps, area_of_interest
	    where st_intersects(fps.geom, area_of_interest.geom)
	    limit 1000000000
	)
	select count(*)
	from footprints
	cd


-- produce a data lice materialized view of LAD boundary with simplified boundary geometry
create materialized view "E06000014_" as (
	select gid, st_simplify(labc.geom, 500) geom, lad21nm
	from local_authority_boundaries labc
	where labc.lad21cd='E06000014'
)


-- POINTCLOUD QUERY CHUNK EDITION
with footprints as (
    select geom_fp, id_fp
    from "E06000026" aoi
    where aoi.id_fp_chunks > 93000 and aoi.id_fp_chunks <= 94000
    limit 1000000
),
fp_buffer as (
    select id_fp, st_buffer(fps.geom_fp, 0.5) geom_fp
    from footprints fps
),
fp_uprn as (
    select fps.id_fp, fps.geom_fp, u.uprn, (u.geom) geom_uprn
    from footprints fps
    left join uprn u
    on st_intersects(fps.geom_fp, u.geom)
),
epc as (
    select *
    from epc e
    where "LOCAL_AUTHORITY" = 'E06000026'
),
fp_uprn_epc as (
    select row_number() over (order by fpu.id_fp) as id_uprn_epc, *
    from fp_uprn fpu
    left join epc e
    on fpu.uprn=e."UPRN"
),
patch_unions as (
    select fpb.id_fp, pc_union(pc_intersection(pa, fpb.geom_fp)) pau
    from uk_lidar_data lp
    inner join fp_buffer fpb on pc_intersects(lp.pa, fpb.geom_fp)
    group by fpb.id_fp
),
building_pc as (
    select
        id_fp,
        st_union(geom) geom_pc,
        max(pc_get(p, 'X')) - min(pc_get(p, 'X')) delta_x,
        max(pc_get(p, 'Y')) - min(pc_get(p, 'Y')) delta_y,
        max(pc_get(p, 'Z')) - min(pc_get(p, 'Z')) delta_z,
        min(pc_get(p, 'Z')) z_min
    from (
        select id_fp, pc_explode(pau) p, pc_explode(pau)::geometry geom
            from patch_unions
        ) po
        group by id_fp
),
building_pc_fp as (
    select
        bpc.id_fp id_fp_bpc,
        bpc.geom_pc,
        fps.geom_fp geom_fp_bpc,
        bpc.delta_x,
        bpc.delta_y,
        bpc.delta_z,
        bpc.z_min,
        greatest(bpc.delta_x, bpc.delta_y, bpc.delta_z) scaling_factor,
        st_numgeometries(geom_pc) num_p_in_pc
    from building_pc bpc
    left join footprints fps on bpc.id_fp = fps.id_fp
    where st_numgeometries(geom_pc) > 100
),
building_pc_fp_epc as (
    select
        id_uprn_epc id_query,
        id_fp,
        uprn,
        "LMK_KEY" id_epc_lmk_key,
        geom_fp,
        geom_uprn,
        geom_pc geom,
        delta_x,
        delta_y,
        delta_z,
        z_min,
        scaling_factor,
        num_p_in_pc,
        "CURRENT_ENERGY_RATING" energy_rating,
        "CURRENT_ENERGY_EFFICIENCY" energy_efficiency
    from fp_uprn_epc fps
    left join building_pc_fp bpf
    on fps.id_fp = bpf.id_fp_bpc
)
select distinct *
from building_pc_fp_epc


-- POINTCLOUD QUERY
with area_of_interest as (
    select st_transform(geom, 27700) geom
    from local_authority_boundaries lab
    where lab.lad21cd = 'E07000178'
),
footprints as (
    select fps.geom geom_fp, fps.gid id_fp
    from footprints_verisk fps, area_of_interest
    where st_intersects(fps.geom, area_of_interest.geom)
    limit 100000
),
fp_buffer as (
    select id_fp, st_buffer(fps.geom_fp, 0.5) geom_fp
    from footprints fps
),
fp_uprn as (
    select fps.id_fp, fps.geom_fp, u.uprn, (u.geom) geom_uprn
    from footprints fps
    left join uprn u
    on st_intersects(fps.geom_fp, u.geom)
),
epc as (
    select *
    from epc e
    where "LOCAL_AUTHORITY" = 'E07000178'
),
fp_uprn_epc as (
    select row_number() over (order by fpu.id_fp) as id_uprn_epc, *
    from fp_uprn fpu
    left join epc e
    on fpu.uprn=e."UPRN"
),
patch_unions as (
    select fpb.id_fp, pc_union(pc_intersection(pa, fpb.geom_fp)) pau
    from uk_lidar_data lp
    inner join fp_buffer fpb on pc_intersects(lp.pa, fpb.geom_fp)
    group by fpb.id_fp
),
building_pc as (
    select
        id_fp,
        st_union(geom) geom_pc,
        max(pc_get(p, 'X')) - min(pc_get(p, 'X')) delta_x,
        max(pc_get(p, 'Y')) - min(pc_get(p, 'Y')) delta_y,
        max(pc_get(p, 'Z')) - min(pc_get(p, 'Z')) delta_z,
        min(pc_get(p, 'Z')) z_min
    from (
        select id_fp, pc_explode(pau) p, pc_explode(pau)::geometry geom
            from patch_unions
        ) po
        group by id_fp
),
building_pc_fp as (
    select
        bpc.id_fp id_fp_bpc,
        bpc.geom_pc,
        fps.geom_fp geom_fp_bpc,
        bpc.delta_x,
        bpc.delta_y,
        bpc.delta_z,
        bpc.z_min,
        greatest(bpc.delta_x, bpc.delta_y, bpc.delta_z) scaling_factor,
        st_numgeometries(geom_pc) num_p_in_pc
    from building_pc bpc
    left join footprints fps on bpc.id_fp = fps.id_fp
    where st_numgeometries(geom_pc) > 50
),
building_pc_fp_epc as (
    select
        id_uprn_epc id_query,
        id_fp,
        uprn,
        "LMK_KEY" id_epc_lmk_key,
        geom_fp,
        geom_uprn,
        geom_pc geom,
        delta_x,
        delta_y,
        delta_z,
        z_min,
        scaling_factor,
        num_p_in_pc,
        "CURRENT_ENERGY_RATING" energy_rating,
        "CURRENT_ENERGY_EFFICIENCY" energy_efficiency
    from fp_uprn_epc fps
    left join building_pc_fp bpf
    on fps.id_fp = bpf.id_fp_bpc
)
select distinct *
from building_pc_fp_epc
