import os
import shutil
import sys

import pandas as pd

# specify paths
DIR_BASE = os.path.abspath('..')
if DIR_BASE not in sys.path:
    sys.path.append(DIR_BASE)

from src.pointcloud_functions import case_specific_json_loader, generate_final_geojson


DIR_OUTPUTS = os.path.join(DIR_BASE, 'outputs')
DIR_EPC = os.path.join(DIR_BASE, 'assets/epc')

DIR_AOIs = os.listdir(DIR_OUTPUTS)


def create_final_results_files(DIR_OUTPUTS, DIR_AOIs, is_public):
    # loop through all AOI
    for AOI in DIR_AOIs:
        if AOI != "example_aoi" and AOI != '.gitkeep':
            print('Creating final results file of: ' + str(AOI))
            DIR_AOI = os.path.join(DIR_OUTPUTS, AOI)
            # get production metrics
            df_production_metrics = pd.read_json(os.path.join(DIR_AOI, 'production_metrics_' + AOI + ' .json'), orient='index')
            # make sure that number of point clouds are complete
            is_enough_pcs = len(os.listdir(os.path.join(DIR_AOI, 'npy_raw'))) \
                            == df_production_metrics.loc["footprints_w_pointclouds"]
            print(str(AOI) + ": number of .npy files: " + str(is_enough_pcs))

            # load filename mapping json
            FILEPATH_MAPPING = os.path.join(DIR_AOI, str('filename_mapping_' + AOI + '.json'))
            gdf_mapping = case_specific_json_loader(FILEPATH_MAPPING, 'filename_mapping')
            # create the geojson with final data
            print("creating final_results.geojson")
            generate_final_geojson(DIR_EPC, DIR_AOI, AOI, gdf_mapping, is_public)
    return


def rename_files(DIR_OUTPUTS, DIR_AOIs):
    # loop through all AOI
    for AOI in DIR_AOIs:
        if AOI != "example_aoi" and AOI != '.gitkeep':
            print('Renaming files of: ' + str(AOI))
            DIR_AOI = os.path.join(DIR_OUTPUTS, AOI)

            # production metrics
            src = os.path.join(DIR_AOI, 'production_metrics_' + AOI + ' .json')
            dst = os.path.join(DIR_AOI, 'production_metrics_' + AOI + '.json')
            os.rename(src, dst)

            # footprint json and uprn json
            src = os.path.join(DIR_AOI, 'footprints_' + AOI + '.json')
            dst = os.path.join(DIR_AOI, 'footprints_' + AOI + '.geojson')
            os.rename(src, dst)
            src = os.path.join(DIR_AOI, 'uprn_' + AOI + '.json')
            dst = os.path.join(DIR_AOI, 'uprn_' + AOI + '.geojson')
            os.rename(src, dst)
    return


def move_non_required_data(DIR_BASE, DIR_OUTPUTS, DIR_AOIs, move_list):
    # make sure outputs_archive folder exists
    DIR_OUTPUTS_ARCHIVE = os.path.join(DIR_BASE, '../outputs_archive')
    if not os.path.isdir(DIR_OUTPUTS_ARCHIVE):
        os.mkdir(DIR_OUTPUTS_ARCHIVE)

    # loop through all AOI
    for AOI in DIR_AOIs:
        if AOI != "example_aoi" and AOI != '.gitkeep':
            print('Moving directories and files of: ' + str(AOI))

            DIR_AOI = os.path.join(DIR_OUTPUTS, AOI)
            # create AOI folder in output_archive directory
            DIR_AOI_ARCHIVE = os.path.join(DIR_OUTPUTS_ARCHIVE, AOI)
            if not os.path.isdir(DIR_AOI_ARCHIVE):
                os.mkdir(DIR_AOI_ARCHIVE)

            for move in move_list:
                src = os.path.join(DIR_AOI, move)
                dst = os.path.join(DIR_AOI_ARCHIVE, move)
                shutil.move(src, dst)

            if move == 'epc' or move == 'filename_mapping':
                ending = '.json'
            else:
                ending = '.geojson'

            src = os.path.join(DIR_AOI, move + '_' + str(AOI) + ending)
            dst = os.path.join(DIR_AOI_ARCHIVE, move + ending)
            shutil.move(src, dst)
    return


# create final_results.geojson
create_final_results_files(DIR_OUTPUTS, DIR_AOIs, is_public=False)
# rename some files
rename_files(DIR_OUTPUTS, DIR_AOIs)
# move non-required data to output_archive folder
move_list = ['epc']
move_non_required_data(DIR_BASE, DIR_OUTPUTS, DIR_AOIs, move_list)
