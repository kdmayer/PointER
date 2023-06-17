import os
import shutil
import sys
import random

import geopandas as gpd
import numpy as np
import pandas as pd

from shapely.geometry import Point

# specify paths
DIR_BASE = os.path.abspath('..')
if DIR_BASE not in sys.path:
    sys.path.append(DIR_BASE)

from utils.visualization import batch_visualization
from utils.aerial_image import get_aerial_image_lat_lon

########################################################################################################################
#
# The following code generates the subsample of point clouds for manual data quality assessment.
# In step 1, the program, plots the selected point clouds as 2D png.
# In step 2, the program, for those point clouds of dubious quality, the program receives a google arial image and
# plots the point clouds as 3D html, to assess the point clouds in detail.
#
########################################################################################################################

# define sample size of quality assessment subsample
sample_size = 5000
# select step: 'step_1' creating 2D .png of subsample or 'step_2' creating 3D .html of "in_doubt" point clouds
step = 'step_2'

# define file paths to directories
DIR_OUTPUTS = os.path.join(DIR_BASE, 'outputs')
DIR_EPC = os.path.join(DIR_BASE, 'assets/epc')
# paths to new directories
DIR_QUALITY_ASSESSMENT = os.path.join(DIR_BASE, 'assets/quality_assessment')
DIR_SUBSET = os.path.join(DIR_QUALITY_ASSESSMENT, 'npy_raw_subset')
DIR_SUBSET_PNGS = os.path.join(DIR_QUALITY_ASSESSMENT, 'entire_subset_pngs')
DIR_IN_DOUBT = os.path.join(DIR_QUALITY_ASSESSMENT, 'in_doubt')
DIR_IN_DOUBT_PNGS = os.path.join(DIR_QUALITY_ASSESSMENT, 'in_doubt_pngs')
DIR_IN_DOUBT_HTMLS = os.path.join(DIR_QUALITY_ASSESSMENT, 'in_doubt_htmls')
DIR_IN_DOUBT_AERIAL = os.path.join(DIR_QUALITY_ASSESSMENT, 'in_doubt_aerial')
DIR_LOW_QUALITY = os.path.join(DIR_QUALITY_ASSESSMENT, 'low_quality')
DIR_LOW_QUALITY_PNGS = os.path.join(DIR_QUALITY_ASSESSMENT, 'low_quality_pngs')
DIR_LOW_QUALITY_HTMLS = os.path.join(DIR_QUALITY_ASSESSMENT, 'low_quality_htmls')
DIR_LOW_QUALITY_AERIAL = os.path.join(DIR_QUALITY_ASSESSMENT, 'low_quality_aerial')
# path to subsample information .json
FILEPATH_DF_FILENAMES = os.path.join(DIR_QUALITY_ASSESSMENT, 'subsample_filename_paths.json')

AOIs = os.listdir(DIR_OUTPUTS)

if step == 'step_1':
    # loop through all AOI and create a list with filepaths of all point clouds
    npy_filename_list = []
    npy_paths_list = []
    for AOI in AOIs:
        if AOI != "example_aoi" and AOI != '.gitkeep':
            DIR_NPY = os.path.join(DIR_OUTPUTS, AOI, 'npy_raw')
            npy_files_list = os.listdir(DIR_NPY)
            [npy_filename_list.append(file) for file in npy_files_list]
            [npy_paths_list.append(os.path.join(DIR_NPY, file)) for file in npy_files_list]

    print('gathered all available point clouds filepaths, total of: ' + str(len(npy_filename_list)))

    # select a subset of point clouds from all point clouds
    id_list = list(np.arange(0, len(npy_filename_list)))
    id_subsample = random.sample(id_list, sample_size)

    npy_filename_subsample = [npy_filename_list[id] for id in id_subsample]
    npy_path_subsample = [npy_paths_list[id] for id in id_subsample]

    # create directory: quality_assessment/entire_subset, /in_doubt, /low_quality
    print('creating quality_assessment directory and sub directories')
    directory_list = [DIR_SUBSET,
                      DIR_SUBSET_PNGS,
                      DIR_IN_DOUBT,
                      DIR_IN_DOUBT_PNGS,
                      DIR_IN_DOUBT_HTMLS,
                      DIR_IN_DOUBT_AERIAL,
                      DIR_LOW_QUALITY,
                      DIR_LOW_QUALITY_PNGS,
                      DIR_LOW_QUALITY_HTMLS,
                      DIR_LOW_QUALITY_AERIAL]

    [os.makedirs(directory, exist_ok=True) for directory in directory_list]

    # create a dataframe that maps filename and filepath
    df = pd.DataFrame({
        'filename': npy_filename_subsample,
        'path': npy_path_subsample
    })
    df.to_json(FILEPATH_DF_FILENAMES)


    #copy all npys to quality assessment directory
    print('copying subset point cloud npys to quality assessment directory')
    for i in np.arange(0, sample_size):
        src = npy_path_subsample[i]
        dst = os.path.join(DIR_QUALITY_ASSESSMENT, 'npy_raw_subset', npy_filename_subsample[i])
        shutil.copy(src, dst)

    # visualize all point clouds of subset as pngs
    batch_visualization(DIR_SUBSET, DIR_SUBSET_PNGS, status_update=True, format='png')


# after manually selecting point clouds in doubt, visualize those in 3D
elif step == 'step_2':
    def get_html_and_aerial_images(DIR_SUBSET, DIR_SUBSET_SUBSET, DIR_PNGS, DIR_HTMLS, DIR_AERIAL):
        filenames_in_doubt = os.listdir(DIR_PNGS)
        filenames_in_doubt = [filename[:-4] for filename in filenames_in_doubt]

        # copy point clouds in doubt
        for filename in filenames_in_doubt:
            src = os.path.join(DIR_SUBSET, filename + '.npy')
            dst = os.path.join(DIR_SUBSET_SUBSET, filename + '.npy')
            shutil.copy(src, dst)

        # visualize all point clouds of subset in doubt as html
        batch_visualization(DIR_SUBSET_SUBSET, DIR_HTMLS, status_update=True, format='html')

        # visualize all point clouds of subset in doubt as aerial image
        seperator_list = [filename.find('_') for filename in filenames_in_doubt]
        point_list = []
        for i, sep in enumerate(seperator_list):
            filename = filenames_in_doubt[i]
            x = float(filename[:sep])
            y = float(filename[sep+1:])
            point_list.append(Point(x, y))

        gdf_in_doubt = gpd.GeoDataFrame({
            'geometry': point_list
        })
        gdf_in_doubt.crs = 27700
        gdf_in_doubt = gdf_in_doubt.to_crs(4326)

        for i, building in enumerate(gdf_in_doubt.iloc):
            cp = building.geometry.centroid
            get_aerial_image_lat_lon(
                latitude=cp.y,
                longitude=cp.x,
                image_name=filenames_in_doubt[i] + '.png',
                horizontal_px=512,
                vertical_px=512,
                scale=1,
                zoom=21,
                save_directory=DIR_AERIAL
            )
        return

    # get html and aerial images of point clouds in doubt
    get_html_and_aerial_images(
        DIR_SUBSET, DIR_IN_DOUBT, DIR_IN_DOUBT_PNGS, DIR_IN_DOUBT_HTMLS, DIR_IN_DOUBT_AERIAL
    )
    # get html and aerial images of point clouds with low quality
    get_html_and_aerial_images(
        DIR_SUBSET, DIR_LOW_QUALITY, DIR_LOW_QUALITY_PNGS, DIR_LOW_QUALITY_HTMLS, DIR_LOW_QUALITY_AERIAL
    )
