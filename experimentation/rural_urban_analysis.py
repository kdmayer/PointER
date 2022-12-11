import os
import sys

import pandas as pd

from sqlalchemy import create_engine

import config
from src.pointcloud_functions import case_specific_json_loader


### IMPORTANT NOTE:
# for this program to work, the 2011 UK small output area boundary shapes need to be inserted into database
# download the data here:
# https://geoportal.statistics.gov.uk/datasets/ons::output-areas-dec-2011-boundaries-ew-bfc/

# check the /documentation/DB_CONTAINER_SETUP.md for an example of how to insert shape file in database

### PATH DEFINITION
# # Load output area rural urban classification data into database
DIR_BASE = os.path.abspath('')
if DIR_BASE not in sys.path:
    sys.path.append(DIR_BASE)

DIR_OUTPUTS = os.path.join(DIR_BASE, '../outputs')
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
        df_ru_ur.to_sql('output_area_rural_urban', con=con, if_exists='replace', index=False)


def insert_footprint_ids_of_data_set_into_db(DIR_OUTPUTS):
    # import result jsons and get footprint ids of footprints with enough points
    dirs = os.listdir(DIR_OUTPUTS)
    df_fp_ids = pd.DataFrame({
        "id_fp": [],
        "num_p_in_pc": []
    })

    for dir in dirs:
        if dir != "example_aoi" and dir != '.gitkeep':
            FILEPATH_MAPPING = os.path.join(DIR_OUTPUTS, dir, str('filename_mapping_' + dir + '.json'))
            gdf_mapping = case_specific_json_loader(FILEPATH_MAPPING, 'filename_mapping')
            df_append = pd.DataFrame({
                "id_fp": gdf_mapping.id_fp,
                "num_p_in_pc":  gdf_mapping.num_p_in_pc
            })
            df_fp_ids = df_fp_ids.append(df_append)
            # ids_fp = list(gdf_mapping.id_fp[gdf_mapping.num_p_in_pc.notna()].unique())
            # [id_fp_list.append(i) for i in ids_fp]

    df_fp_ids = df_fp_ids.dropna()
    df_fp_ids = df_fp_ids.drop_duplicates()

    with engine.connect() as con:
        df_fp_ids.to_sql('footprint_ids_in_data_set', con=con, if_exists='replace', index=False)


# insert footprint ids of database into database
insert_footprint_ids_of_data_set_into_db(DIR_OUTPUTS)

# insert classification of 2011 UK small areas in rural / urban into database
insert_rural_urban_classes_into_db(DIR_BASE, FILE_RURAL_URBAN)
