import os
import sys

import geopandas as gpd
import pandas as pd

from sqlalchemy import create_engine

# specify paths
DIR_BASE = os.path.abspath('..')
if DIR_BASE not in sys.path:
    sys.path.append(DIR_BASE)

from src.pointcloud_functions import case_specific_json_loader
import config


def db_import_epc_all(DIR_EPC, engine):
    EPC_FILENAMES = os.listdir(DIR_EPC)
    for i, epc_filename in enumerate(EPC_FILENAMES):
        if epc_filename != '.gitkeep':
            print('importing: ' + str(epc_filename) + ' - file ' + str(i) + ' out of ' + str(len(EPC_FILENAMES)))
            file_path = os.path.join(DIR_EPC, epc_filename)
            df = pd.read_csv(file_path)

            if MODE == "reduced":
                df_reduced = pd.DataFrame({
                    'LMK_KEY': df["LMK_KEY"],
                    'UPRN': df["UPRN"],
                    'LOCAL_AUTHORITY': df["LOCAL_AUTHORITY"],
                    'CURRENT_ENERGY_RATING': df["CURRENT_ENERGY_RATING"],
                    'POTENTIAL_ENERGY_RATING': df["POTENTIAL_ENERGY_RATING"],
                    'CURRENT_ENERGY_EFFICIENCY': df["CURRENT_ENERGY_EFFICIENCY"],
                    'POTENTIAL_ENERGY_EFFICIENCY': df["POTENTIAL_ENERGY_EFFICIENCY"],
                    'ENERGY_CONSUMPTION_CURRENT': df["ENERGY_CONSUMPTION_POTENTIAL"],
                    'CO2_EMISSIONS_CURRENT': df["CO2_EMISSIONS_CURRENT"],
                    'CO2_EMISSIONS_POTENTIAL': df["CO2_EMISSIONS_POTENTIAL"]
                })
                df_import = df_reduced.copy()
                db_name = "epc_all"
                # delete temporary dataframes to avoid memory overflow
                del df_reduced

            elif MODE == "full":
                df_import = df.copy()
                db_name = 'epc_reduced_all'
                # delete temporary dataframes to avoid memory overflow
                del df

            # insert information into database
            with engine.connect() as con:
                df_import.to_sql(db_name, con=con, if_exists='append', index=False)

            # delete temporary dataframes to avoid memory overflow
            del df_import
    return


def db_import_verisk_link_data(verisk_link_filepath, engine):
    # load verisk link data into database
    df = pd.read_csv(verisk_link_filepath)
    with engine.connect() as con:
        df.to_sql('verisk_uprn_link', con=con, index=False)
    return


def generate_final_results_verisk_uprn(engine):
    sql_query = """
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
    """

    # actual fetching step
    gdf_final_results = gpd.GeoDataFrame.from_postgis(sql_query, engine)
    return gdf_final_results


def final_results_verisk_uprn(DIR_OUTPUTS, DIR_AOIs, engine, is_public):
    # loop through all AOI
    for AOI in DIR_AOIs:
        if AOI != "example_aoi" and AOI != '.gitkeep':
            print('Creating final results file of: ' + str(AOI))
            DIR_AOI = os.path.join(DIR_OUTPUTS, AOI)
            # get production metrics
            filepath_production_metrics = os.path.join(DIR_AOI, 'production_metrics_' + AOI + ' .json')
            if os.path.isfile(filepath_production_metrics):
                df_production_metrics = pd.read_json(filepath_production_metrics, orient='index')
                # make sure that number of point clouds are complete
                is_enough_pcs = len(os.listdir(os.path.join(DIR_AOI, 'npy_raw'))) \
                                == df_production_metrics.loc["footprints_w_pointclouds"]
                print(str(AOI) + ": number of .npy files: " + str(is_enough_pcs))

            # load filename mapping json
            FILEPATH_MAPPING = os.path.join(DIR_AOI, str('filename_mapping' + '.json'))
            df_mapping = case_specific_json_loader(FILEPATH_MAPPING, 'filename_mapping')

            df_to_db = pd.DataFrame({
                'id_fp': df_mapping.id_fp,
                'pc_file_name': df_mapping.file_name,
                'num_p_in_pc': df_mapping.num_p_in_pc
            })
            df_to_db = df_to_db.drop_duplicates()

            # insert footprint id to filename point cloud mapping into db
            print('inserting footprint - point cloud mapping of ' + AOI + ' into database')
            with engine.connect() as con:
                df_to_db.to_sql('fp_to_pc', con=con, if_exists='replace', index=False)

            print('getting final results from database for ' + AOI)
            # get final results geodataframe by calling sql query in db
            gdf_final_results = generate_final_results_verisk_uprn(engine)

            # drop address data because of license
            if is_public == True:
                gdf_final_results = gdf_final_results.drop(["ADDRESS1", "ADDRESS2", "ADDRESS3", "POSTCODE"], axis=1)
                gdf_final_results = gdf_final_results.drop(["geometry"], axis=1)

            # save final results as json
            print('saving final results of ' + AOI)
            file_path = os.path.join(DIR_BASE, 'outputs', AOI, 'final_result_verisk_uprn_' + AOI + '.geojson')
            gdf_final_results.to_file(file_path, driver="GeoJSON")

            # calculate number of footprints with epc
            num_fp_w_epc = gdf_final_results[gdf_final_results["LMK_KEY"].notna()]["id_fp"].nunique()
            print("number of unique footprints with EPC data: " + str(num_fp_w_epc))
    return


# define directories
DIR_OUTPUTS = os.path.join("/home/ubuntu/outputs_archive")
DIR_AOIs = os.listdir(DIR_OUTPUTS)
DIR_EPC = os.path.join(DIR_BASE, 'assets', 'epc')
DIR_FOOTPRINTS = os.path.join(DIR_BASE, 'assets', 'footprints')

# initialize connection to database
DB_CONNECTION_URL = config.DATABASE_URL
engine = create_engine(DB_CONNECTION_URL, echo=False)

# 1) insert EPC data of the AOIs of our dataset into database. process will take a lot of time (imports ~15 GB of data)
# select mode
MODE = "reduced"  # "reduced" subset of epc features or: "full" all epc features
db_import_epc_all(DIR_EPC, engine)

# 2) import verisk link data to database. this process will take a lot of time (imports ~3.6 GB of data)
file_name = "UKBuildings_Edition_13_ABC_link_file.csv"
verisk_link_filepath = os.path.join(DIR_FOOTPRINTS)
db_import_verisk_link_data(verisk_link_filepath, engine)

# 3) create final_results.geojson using verisk UPRN link and the full range of EPC features
final_results_verisk_uprn(DIR_OUTPUTS, DIR_AOIs, engine, is_public=True)

