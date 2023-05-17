------------------------------------------------------------------------------------------------------------------------
-- This code is used to conduct the representativity analysis described in the paper (chapter "Technical Validation")
------------------------------------------------------------------------------------------------------------------------

-- representivity of property_area our DATASET
with unique_footprints as (
	select distinct id_fp
	from footprint_ids_in_data_set_uprn_verisk fiidsuv
	where fiidsuv.num_p_in_pc notnull
),
footprints_dataset as (
	select *
	from unique_footprints ufps
	left join footprints_verisk fv on ufps.id_fp=fv.gid
),
histogram as (
   -- select width_bucket(fv.height, min, max, 19) as bucket,
		select width_bucket(fv.property_area  , 0, 200, 10) as bucket,
          -- int4range(min(fv.height)::INTEGER, max(fv.height)::INTEGER, '[]') as range,
		  int4range(min(fv.property_area)::INTEGER, max(fv.property_area)::INTEGER, '[]') as range,
          count(*) as freq
     from footprints_dataset fv
 group by bucket
 order by bucket
)
select bucket, range, freq,
	repeat('■',
    	(freq::float
    		/ max(freq) over()
            * 30
        )::int
	) as bar
from histogram;


-- representivity of property_area ENGLAND
with footprints_england as (
	select *
	from footprint_ids_in_england fiie
	left join footprints_verisk fv on fiie.gid=fv.gid
),
histogram as (
   -- select width_bucket(fv.height, min, max, 19) as bucket,
		select width_bucket(fv.property_area  , 0, 200, 10) as bucket,
          -- int4range(min(fv.height)::INTEGER, max(fv.height)::INTEGER, '[]') as range,
		  int4range(min(fv.property_area)::INTEGER, max(fv.property_area)::INTEGER, '[]') as range,
          count(*) as freq
     from footprints_england fv
 group by bucket
 order by bucket
)
select bucket, range, freq,
	repeat('■',
    	(freq::float
    		/ max(freq) over()
            * 30
        )::int
	) as bar
from histogram;


-- representivity of building_area our DATASET
with unique_footprints as (
	select distinct id_fp
	from footprint_ids_in_data_set_uprn_verisk fiidsuv
	where fiidsuv.num_p_in_pc notnull
),
footprints_dataset as (
	select *
	from unique_footprints ufps
	left join footprints_verisk fv on ufps.id_fp=fv.gid
),
histogram as (
   -- select width_bucket(fv.height, min, max, 19) as bucket,
		select width_bucket(fv.building_area  , 0, 500, 10) as bucket,
          -- int4range(min(fv.height)::INTEGER, max(fv.height)::INTEGER, '[]') as range,
		  int4range(min(fv.building_area)::INTEGER, max(fv.building_area)::INTEGER, '[]') as range,
          count(*) as freq
     from footprints_dataset fv
 group by bucket
 order by bucket
)
select bucket, range, freq,
	repeat('■',
    	(freq::float
    		/ max(freq) over()
            * 30
        )::int
	) as bar
from histogram;


-- representivity of building_area ENGLAND
with footprints_england as (
	select *
	from footprint_ids_in_england fiie
	left join footprints_verisk fv on fiie.gid=fv.gid
),
histogram as (
   -- select width_bucket(fv.height, min, max, 19) as bucket,
		select width_bucket(fv.building_area  , 0, 500, 10) as bucket,
          -- int4range(min(fv.height)::INTEGER, max(fv.height)::INTEGER, '[]') as range,
		  int4range(min(fv.building_area)::INTEGER, max(fv.building_area)::INTEGER, '[]') as range,
          count(*) as freq
     from footprints_england fv
 group by bucket
 order by bucket
)
select bucket, range, freq,
	repeat('■',
    	(freq::float
    		/ max(freq) over()
            * 30
        )::int
	) as bar
from histogram;



-- representivity of HEIGHT our DATASET
with unique_footprints as (
	select distinct id_fp
	from footprint_ids_in_data_set_uprn_verisk fiidsuv
	where fiidsuv.num_p_in_pc notnull
),
footprints_dataset as (
	select *
	from unique_footprints ufps
	left join footprints_verisk fv on ufps.id_fp=fv.gid
),
histogram as (
	select width_bucket(fv.height  , 0, 20, 10) as bucket,
    	int4range(min(fv.height)::INTEGER, max(fv.height)::INTEGER, '[]') as range,
        count(*) as freq
    from footprints_dataset fv
 group by bucket
 order by bucket
)
select bucket, range, freq,
	repeat('■',
    	(freq::float
    		/ max(freq) over()
            * 30
        )::int
	) as bar
from histogram;


-- representivity of HEIGHT ENGLAND
with footprints_england as (
	select *
	from footprint_ids_in_england fiie
	left join footprints_verisk fv on fiie.gid=fv.gid
),
histogram as (
	select width_bucket(fv.height  , 0, 20, 10) as bucket,
    	int4range(min(fv.height)::INTEGER, max(fv.height)::INTEGER, '[]') as range,
        count(*) as freq
    from footprints_england fv
 group by bucket
 order by bucket
)
select bucket, range, freq,
	repeat('■',
    	(freq::float
    		/ max(freq) over()
            * 30
        )::int
	) as bar
from histogram;


-- representivity of AGE in footprints our DATASET
with unique_footprints as (
	select distinct id_fp
	from footprint_ids_in_data_set_uprn_verisk fiidsuv
	where fiidsuv.num_p_in_pc notnull
),
footprints_dataset as (
	select *
	from unique_footprints ufps
	left join footprints_verisk fv on ufps.id_fp=fv.gid
),
analytics_attributes as (
	select fp.age attr -- select column
	from footprints_dataset fp -- select table
)
select attr, count(attr)
from analytics_attributes
group by attr

-- representivity of AGE in footprints ENGLAND
with footprints_england as (
	select *
	from footprint_ids_in_england fiie
	left join footprints_verisk fv on fiie.gid=fv.gid
),
analytics_attributes as (
	select fp.age attr -- select column
	from footprints_england fp -- select table
)
select attr, count(attr)
from analytics_attributes
group by attr


-- representivity of USE in footprints our DATASET
with unique_footprints as (
	select distinct id_fp
	from footprint_ids_in_data_set_uprn_verisk fiidsuv
	where fiidsuv.num_p_in_pc notnull
),
footprints_dataset as (
	select *
	from unique_footprints ufps
	left join footprints_verisk fv on ufps.id_fp=fv.gid
),
analytics_attributes as (
	select fp.use attr -- select column
	from footprints_dataset fp -- select table
)
select attr, count(attr)
from analytics_attributes
group by attr

-- representivity of USE in footprints ENGLAND
with footprints_england as (
	select *
	from footprint_ids_in_england fiie
	left join footprints_verisk fv on fiie.gid=fv.gid
),
analytics_attributes as (
	select fp.use attr -- select column
	from footprints_england fp -- select table
)
select attr, count(attr)
from analytics_attributes
group by attr


-- rural urban of ENGLAND
-- > leads to a higher number of buildings than the other representativity analysis,
-- because intersection of output area with verisk footprint leads to duplicate count
with ruoa_in_england as (
	select *
	from ruoa_classification rc
	where substring(rc.oaid, 1, 1)='E'
)
select classification_10 , count(classification_10), sum(num_fp), code
from ruoa_in_england
group by classification_10, code

-- rural urban of DATASET
f footprints in dataset
with footprint_codes_distinct as (
	select distinct id_fp, code, oaid_code
	from ruoa_classification_fps_in_dataset rcfid
)
select code, oaid_code, count(*)
from footprint_codes_distinct
group by code, oaid_code


-- representivity of EPC rating DATASET
with unique_footprints as (
	select distinct id_fp, uprn
	from footprint_ids_in_data_set_uprn_verisk fiidsuv
	where fiidsuv.num_p_in_pc notnull
),
footprints_dataset as (
	select uprn, era."CURRENT_ENERGY_RATING" epc
	from unique_footprints ufps
	left join epc_reduced_all era on ufps.uprn=era."UPRN"
),
analytics_attributes as (
	select fp.epc attr -- select column
	from footprints_dataset fp -- select table
)
select attr, count(attr)
from analytics_attributes
group by attr


-- representivity of EPC rating ENGLAND
with unique_footprints as (
	select distinct gid, upn
	from footprint_ids_in_england fiie
),
footprints_with_uprn as (
	select uf.gid, vul.uprn
	from unique_footprints uf
	left join verisk_uprn_link vul on uf.upn=vul.upn
),
footprints_england as (
	select uprn, era."CURRENT_ENERGY_RATING" epc
	from footprints_with_uprn fwu
	left join epc_reduced_all era on fwu.uprn=era."UPRN"
),
analytics_attributes as (
	select fp.epc attr -- select column
	from footprints_england fp -- select table
)
select attr, count(attr)
from analytics_attributes
group by attr


-- representivity of EPC rating ENGLAND ALTERNATIVE
select era."CURRENT_ENERGY_RATING", count(era."CURRENT_ENERGY_RATING")
from epc_reduced_all era
where substring(era."LOCAL_AUTHORITY", 1, 1)='E'
group by era."CURRENT_ENERGY_RATING"

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
		  int4range(min(fv.property_area)::INTEGER, max(fv.property_area)::INTEGER, '[]') as range,
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