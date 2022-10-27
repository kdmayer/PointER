import os
import time

from sqlalchemy import create_engine

import config
from pointcloud_functions import \
    load_laz_pointcloud_into_database, \
    add_floor_points_to_points_in_gdf, \
    crop_and_fetch_pointclouds_per_building, \
    save_lidar_numpy_list
from utils.utils import convert_multipoint_to_numpy, check_directory_paths
from utils.visualization import visualize_single_3d_point_cloud
from utils.aerial_image import get_aerial_image_lat_lon

######################   Configurations   #####################################
# Define configuration
AREA_OF_INTEREST_CODE = 'E06000014'
BUILDING_BUFFER_METERS = 0.5
MAX_NUMBER_OF_FOOTPRINTS = 1000  # define how many footprints should be used for cropping, use "None" to use all footprints
POINT_COUNT_THRESHOLD = 1000  # define minimum points in pointcloud, smaller pointclouds are dismissed
NUMBER_EXAMPLE_VISUALIZATIONS = 100  # define how many example 3D plots should be created
STANDARD_CRS = 27700  # define the CRS. needs to be same for footprints and lidar data

# Define project base directory and paths
DIR_BASE = os.getcwd()
DIR_ASSETS = os.path.join(os.path.dirname(DIR_BASE), 'assets')
DIR_OUTPUTS = os.path.join(DIR_BASE, 'outputs')
DIR_BUILDING_FOOTPRINTS = os.path.join(DIR_ASSETS, "aoi")
DIR_LAZ_FILES = os.path.join(DIR_ASSETS, "uk_lidar_data")
DIR_VISUALIZATION = os.path.join(DIR_ASSETS, "example_pointclouds")
DIR_AERIAL_IMAGES = os.path.join(DIR_ASSETS, "aerial_image_examples")
DIR_NPY = os.path.join(DIR_ASSETS, "pointcloud_npy")

# check that all required directories exist
check_directory_paths([DIR_ASSETS, DIR_OUTPUTS, DIR_BUILDING_FOOTPRINTS, DIR_LAZ_FILES, \
                       DIR_NPY, DIR_VISUALIZATION, DIR_AERIAL_IMAGES])

DB_TABLE_NAME_LIDAR = 'uk_lidar_data'
DB_TABLE_NAME_FOOTPRINTS = 'footprints_verisk'
DB_TABLE_NAME_UPRN = 'uprn'
DB_TABLE_NAME_AREA_OF_INTEREST = 'local_authority_boundaries'

# Intialize connection to database
db_connection_url = config.DATABASE_URL
engine = create_engine(db_connection_url, echo=False)

#####################   Actual Pipeline   #####################################
# # todo: include approach which allows appending new data to database. difficulty: making sure that there are no duplicates

# todo: check if should be deleted
# # load footprint geojsons into database
# gdf_footprints = load_geojson_footprints_into_database(
#     DIR_BUILDING_FOOTPRINTS, DB_TABLE_NAME_FOOTPRINTS, engine, STANDARD_CRS
# )

# Load point cloud data into database
load_laz_pointcloud_into_database(DIR_LAZ_FILES, DB_TABLE_NAME_LIDAR)

# todo: check if should be deleted
# # Add geoindex to footprint and lidar tables
# add_geoindex_to_databases(DB_TABLE_NAME_FOOTPRINTS, DB_TABLE_NAME_LIDAR)

# adapt NUMBER_OF_FOOTPRINTS to use all footprints if None
if MAX_NUMBER_OF_FOOTPRINTS == None:
    MAX_NUMBER_OF_FOOTPRINTS = 1000000000  # 1 billion, which is more than UKs building stock

# Fetch cropped point clouds from database
gdf = crop_and_fetch_pointclouds_per_building(
    AREA_OF_INTEREST_CODE, BUILDING_BUFFER_METERS, MAX_NUMBER_OF_FOOTPRINTS, POINT_COUNT_THRESHOLD, engine)

# add floor points to building pointcloud
gdf = add_floor_points_to_points_in_gdf(gdf)

# todo: select raw or scaled lidar to npy
# # Determine scaling factor (max delta_x/delta_y/delta_z of all points)
# scaling_factor = get_scaling_factor(gdf)
# # Convert fetched building point clouds to numpy
# lidar_numpy_list = pointcloud_gdf_to_numpy(gdf, scaling_factor, POINT_COUNT_THRESHOLD)

# Save raw pointcloud without threshhold or scaling
lidar_numpy_list = list(gdf.geom.apply(convert_multipoint_to_numpy))
# Save building point clouds as npy
save_lidar_numpy_list(lidar_numpy_list, gdf)
# Visualize example data before and after normalization
for i, lidar_pc in enumerate(lidar_numpy_list):
    if i <= NUMBER_EXAMPLE_VISUALIZATIONS:
        pce_file_name = str(gdf.iloc[i].fp_geom.centroid.x) + "_" + \
                        str(gdf.iloc[i].fp_geom.centroid.y) + ".html"
        save_path = os.path.join(DIR_VISUALIZATION, pce_file_name)
        visualize_single_3d_point_cloud(
            lidar_pc,
            title=str(i),
            save_path=save_path,
            show=False
        )

# Visualize example aerial images
gdf_lat_lon = gdf.to_crs(4326)

for i, building in enumerate(gdf_lat_lon.iloc):
    ai_file_name = str(gdf.iloc[i].fp_geom.centroid.x) + "_" + \
                    str(gdf.iloc[i].fp_geom.centroid.y) + ".png"
    if i <= NUMBER_EXAMPLE_VISUALIZATIONS:
        cp = building.geom.centroid
        get_aerial_image_lat_lon(
            latitude=cp.y,
            longitude=cp.x,
            image_name=ai_file_name,
            horizontal_px=512,
            vertical_px=512,
            scale=1,
            zoom=21,
            save_directory=DIR_AERIAL_IMAGES
        )
