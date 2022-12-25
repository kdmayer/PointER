import os
import sys
import psycopg2

import pandas as pd

from sqlalchemy import create_engine

DIR_BASE = os.path.abspath('..')
if DIR_BASE not in sys.path:
    sys.path.append(DIR_BASE)

import config
from src.pointcloud_functions import case_specific_json_loader

### IMPORTANT NOTE:
# for this program to work, the 2011 UK small output area boundary shapes need to be inserted into database
# download the data here:
# https://geoportal.statistics.gov.uk/datasets/ons::output-areas-dec-2011-boundaries-ew-bfc/

# check the /documentation/DB_CONTAINER_SETUP.md for an example of how to insert shape file in database
# ogr2ogr -nln output_area_boundaries -nlt PROMOTE_TO_MULTI -lco GEOMETRY_NAME=geom -lco FID=gid -lco PRECISION=NO
# -f PostgreSQL "PG:dbname='cs224w' host='localhost' port='5432' user='vagrant' password='mypassword'"
# /home/vagrant/CS224W_LIDAR/assets/rural_urban/Output_Areas_\(Dec_2011\)_Boundaries_EW_\(BFC\).shp

### PATH DEFINITION
DIR_OUTPUTS = os.path.join('/home/vagrant/data_share', '/outputs')
DIR_RURAL_URBAN = os.path.join(DIR_BASE, "assets", "rural_urban")
# categorization of small area geographies into rural and urban classes
# download data at:
# https://www.gov.uk/government/statistics/2011-rural-urban-classification-lookup-tables-for-all-geographies
# convert .ods format to .xlsx format
FILE_RURAL_URBAN = "Rural_Urban_Classification_2011_lookup_tables_for_small_area_geographies.xlsx"

### DATA BASE CONNECTION
# Intialize connection to database
DB_CONNECTION_URL = config.DATABASE_URL
engine = create_engine(DB_CONNECTION_URL, echo=False)


def insert_rural_urban_classes_into_db(DIR_BASE, FILE_RURAL_URBAN):
    # # Load output area rural urban classification data into database
    file_path = os.path.join(DIR_BASE, FILE_RURAL_URBAN)
    df_ru_ur = pd.read_excel(file_path, sheet_name="OA11", skiprows=2)

    # clean up data
    for col in df_ru_ur.columns:
        for i, row in enumerate(df_ru_ur[col].iloc):
            data = str(df_ru_ur.loc[i, col])
            df_ru_ur.loc[i, col] = data.replace("\xa0", "")

    with engine.connect() as con:
        df_ru_ur.to_sql('output_area_rural_urban_classification', con=con, if_exists='replace', index=False)


def insert_footprint_ids_of_data_set_into_db(DIR_OUTPUTS):
    # import result jsons and get footprint ids of footprints with enough points
    dirs = os.listdir(DIR_OUTPUTS)
    df_fp_ids = pd.DataFrame({
        "id_fp": [],
        "num_p_in_pc": []
    })

    for dir in dirs:
        if dir != "example_aoi" and dir != '.gitkeep' and dir[-4:] != ".zip":
            FILEPATH_MAPPING = os.path.join(DIR_OUTPUTS, dir, str('filename_mapping_' + dir + '.json'))
            gdf_mapping = case_specific_json_loader(FILEPATH_MAPPING, 'filename_mapping')
            # get footprint ids in dataset and number of points in their point cloud
            df_append = pd.DataFrame({
                "id_fp": gdf_mapping.id_fp,
                "num_p_in_pc": gdf_mapping.num_p_in_pc
            })

            print('Adding ' + str(dir) + ' to footprint ids - ' + '\n' +
                  str(len(df_append)) + ' fps' + '\n' +
                  str(len(df_append.drop_duplicates())) + ' unique fp' + '\n' +
                  str(len(df_append.dropna().drop_duplicates())) + ' unique fp with points')

            # drop duplicate information and footprints without enough points
            df_append = df_append.dropna()
            df_append = df_append.drop_duplicates()

            # Calculate #UPRN per FP
            gdf_uprn = pd.DataFrame({
                "id_fp": gdf_mapping.id_fp,
                "num_uprn": gdf_mapping.uprn
            })
            gdf_uprn = gdf_uprn.groupby('id_fp').count()

            # calculate #EPC per FP
            gdf_epc = pd.DataFrame({
                "id_fp": gdf_mapping.id_fp,
                "num_epc": gdf_mapping.id_id_epc_lmk_key
            })
            gdf_epc = gdf_epc.groupby('id_fp').count()

            # add number of EPC and UPRN information to footprint ids
            df_append = df_append.join(gdf_epc, on='id_fp', how='left')
            df_append = df_append.join(gdf_uprn, on='id_fp', how='left')

            df_fp_ids = df_fp_ids.append(df_append)
            # ids_fp = list(gdf_mapping.id_fp[gdf_mapping.num_p_in_pc.notna()].unique())
            # [id_fp_list.append(i) for i in ids_fp]


    with engine.connect() as con:
        df_fp_ids.to_sql('footprint_ids_in_data_set_with_epc_uprn', con=con, if_exists='replace', index=False)


def run_sql_query(db_connection_url, sql_query):
    connection_psycopg2 = psycopg2.connect(db_connection_url)
    cursor = connection_psycopg2.cursor()
    cursor.execute(sql_query)
    response = cursor.fetchall()
    connection_psycopg2.commit()
    connection_psycopg2.close()
    return response


def create_rural_urban_table_in_db(db_connection_url):
    sql_query = """
        create table rural_urban_output_area as
        select
            gid,
            oa11cd oaid,
            oaru."Rural Urban Classification 2011 code" classification_code,
            oaru."Rural Urban Classification 2011 (10 fold)" classification_10,
            oaru."Rural Urban Classification 2011 (2 fold)" classification_2,
            st_setsrid(geom, 27700) geom
        from output_area_boundaries oab
        left join output_area_rural_urban_classification oaru on oab.oa11cd=oaru."Output Area 2011 Code"
    """

    sql_query_geoindex = """
        create index rural_urban_output_area_geom_geom_idx on rural_urban_output_area using gist(geom);
    """

    run_sql_query(db_connection_url, sql_query)
    run_sql_query(db_connection_url, sql_query_geoindex)
    return


def create_table_footprints_rural_urban(db_connection_url):
    sql_query = """
        -- rural urban analysis clustered by output area
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
    """
    run_sql_query(db_connection_url, sql_query)
    return


def create_table_footprints_w_aoi_rural_urban(db_connection_url):
    sql_query = """
        create materialized view ru_classification_aoi_fp as 
            with lads as (
                select distinct lab.lad21cd
                from local_authority_boundaries lab 
            ),
            ruoa_classification_aoi as (
                select 
                    count(fv.gid) num_fp,
                    lab.lad21cd lad21cd,
                    -- oab.oa11cd id_oab,
                    oaruc."Rural Urban Classification 2011 code" code,
                    oaruc."Rural Urban Classification 2011 (10 fold)" classification_10
                from footprints_verisk fv 
                left join local_authority_boundaries lab on st_intersects(fv.geom, lab.geom)
                left join output_area_boundaries oab on st_intersects(fv.geom, oab.geom)
                left join output_area_rural_urban_classification oaruc on oab.oa11cd = oaruc."Output Area 2011 Code" 
                group by lad21cd, code, classification_10 
            )
            select *
            from ruoa_classification_aoi

        """
    run_sql_query(db_connection_url, sql_query)
    return


def create_rural_urban_classification_of_footprints_in_data_set(db_connection_url):
    sql_query = """
        create materialized view ruoa_classification_fps_in_dataset_with_epc_uprn as 
        with footprints as (
            select 
                fv.gid id_fp,
                fv.geom geom
            from footprint_ids_in_data_set_with_epc_uprn fiids 
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
    """
    run_sql_query(db_connection_url, sql_query)
    return


def analyze_rural_urban_footprints_in_dataset(db_connection_url):
    sql_query = """    
        -- rural urban of footprints in dataset 
        with footprint_codes_distinct as (
            select distinct id_fp, code, oaid_code
            from ruoa_classification_fps_in_dataset rcfid 
        )
        select code, oaid_code, count(*)
        from footprint_codes_distinct 
        group by code, oaid_code 
    """
    response = run_sql_query(db_connection_url, sql_query)
    return response


# insert footprint ids of database into database
# insert_footprint_ids_of_data_set_into_db(DIR_OUTPUTS)

# create a materialized view of footprints in dataset and their rural urban classification
create_rural_urban_classification_of_footprints_in_data_set(DB_CONNECTION_URL)

# analyse the footprints in dataset's rural urban classification
# response = analyze_rural_urban_footprints_in_dataset(DB_CONNECTION_URL)

# insert classification of 2011 UK small areas in rural / urban into database
# insert_rural_urban_classes_into_db(DIR_RURAL_URBAN, FILE_RURAL_URBAN)

# create rural urban table with boundaries - add rural urban information to output area boundaries
# create_rural_urban_table_in_db(DB_CONNECTION_URL)

# create_table_footprints_w_aoi_rural_urban(DB_CONNECTION_URL)
