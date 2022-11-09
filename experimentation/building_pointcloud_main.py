# Import python packages
import os
import sys
import laspy

import geopandas as gpd
import pandas as pd

from sqlalchemy import create_engine
from datetime import datetime


# Add parent folder to path, so that notebook can find .py scripts
DIR_BASE = os.path.abspath(os.path.join('..'))
if DIR_BASE not in sys.path:
    sys.path.append(DIR_BASE)

# Import functions from own .py scripts
import config
from pointcloud_functions import \
    add_geoindex_to_databases, \
    load_laz_pointcloud_into_database, \
    add_floor_points_to_points_in_gdf, \
    crop_and_fetch_pointclouds_per_building, \
    save_lidar_numpy_list

from utils.utils import convert_multipoint_to_numpy, check_directory_paths, file_name_from_polygon_list
from utils.visualization import visualize_single_3d_point_cloud
from utils.aerial_image import get_aerial_image_lat_lon


######################   Configurations   #####################################
# Define pointcloud parameters
AREA_OF_INTEREST_CODE = 'E07000178' #'E08000026' # UK local authority boundary code to specify area of interest (AOI)
BUILDING_BUFFER_METERS = 0.5 # buffer around building footprint in meters
MAX_NUMBER_OF_FOOTPRINTS = None  # define how many footprints should be created. Use "None" to use all footprints in AOI
POINT_COUNT_THRESHOLD = 50  # define minimum points in pointcloud, smaller pointclouds are dismissed
NUMBER_EXAMPLE_VISUALIZATIONS = 50  # define how many example 3D plots should be created

# Define project base directory and paths
# DIR_BASE = os.getcwd() # in jupyter, use a different approach (above) to determine project DIR
DIR_ASSETS = os.path.join(DIR_BASE, 'assets')
DIR_OUTPUTS = os.path.join(DIR_BASE, 'outputs')

DIR_LAZ_FILES = os.path.join(DIR_ASSETS, "uk_lidar_data")
DIR_EPC = os.path.join(DIR_ASSETS, "epc")
DIR_VISUALIZATION = os.path.join(DIR_ASSETS, "example_pointclouds")
DIR_AERIAL_IMAGES = os.path.join(DIR_ASSETS, "aerial_image_examples")

# Create a new output folder for the defined area of interest
DIR_AOI_OUTPUT = os.path.join(DIR_OUTPUTS, AREA_OF_INTEREST_CODE)
if os.path.isdir(DIR_AOI_OUTPUT):
    print('output for this area of interest already exists. delete or choose other area code')
else:
    os.mkdir(DIR_AOI_OUTPUT)
DIR_NPY = os.path.join(DIR_AOI_OUTPUT, 'npy_raw')
if not os.path.isdir(DIR_NPY): os.mkdir(DIR_NPY)


# Check that all required directories exist
check_directory_paths([DIR_ASSETS, DIR_OUTPUTS, DIR_LAZ_FILES, DIR_VISUALIZATION, DIR_AERIAL_IMAGES, DIR_AOI_OUTPUT, DIR_NPY])

DB_TABLE_NAME_LIDAR = 'uk_lidar_data'
DB_TABLE_NAME_FOOTPRINTS = 'footprints_verisk'
DB_TABLE_NAME_UPRN = 'uprn'
DB_TABLE_NAME_AREA_OF_INTEREST = 'local_authority_boundaries'

# Intialize connection to database
db_connection_url = config.DATABASE_URL
engine = create_engine(db_connection_url, echo=False)

# Test connection to database
with engine.connect() as con:
    res = con.execute('SELECT * FROM footprints_verisk LIMIT 1')
print(res.all())

# Load footprint geojsons into database (only required if they haven't already been uploaded already)
# STANDARD_CRS = 27700
# DIR_BUILDING_FOOTPRINTS = os.path.join(DIR_ASSETS, "aoi")
# gdf_footprints = load_geojson_footprints_into_database(
#     DIR_BUILDING_FOOTPRINTS, DB_TABLE_NAME_FOOTPRINTS, engine, STANDARD_CRS
# )

# Load point cloud data into database
# Unpacks LAZ-files and inserts all newly unpacked LAS-files into the database
# Existing LAS-files in directory are considered to be in the database already
print("Starting LAZ to DB", datetime.now().strftime("%H:%M:%S"))
load_laz_pointcloud_into_database(DIR_LAZ_FILES, DB_TABLE_NAME_LIDAR)

# Load EPC data into database
file_path = os.path.join(DIR_EPC, AREA_OF_INTEREST_CODE + '.csv')
df_epc = pd.read_csv(file_path)
with engine.connect() as con:
    df_epc.to_sql('epc', con=con, if_exists='replace', index=False)

# Add geoindex to footprint and lidar tables and vacuum table
print("Starting geoindexing", datetime.now().strftime("%H:%M:%S"))
db_table_names = [DB_TABLE_NAME_LIDAR, DB_TABLE_NAME_FOOTPRINTS, DB_TABLE_NAME_UPRN, DB_TABLE_NAME_AREA_OF_INTEREST]
db_is_lidar = [1, 0, 0, 0]
add_geoindex_to_databases(config.DATABASE_URL, db_table_names, db_is_lidar)

# Adapt NUMBER_OF_FOOTPRINTS to use all footprints if None
if MAX_NUMBER_OF_FOOTPRINTS == None:
    MAX_NUMBER_OF_FOOTPRINTS = 1000000000  # 1 billion, which is more than UKs building stock

# Fetch cropped point clouds from database
print("Starting point cloud cropping", datetime.now().strftime("%H:%M:%S"))
gdf = crop_and_fetch_pointclouds_per_building(
    AREA_OF_INTEREST_CODE, BUILDING_BUFFER_METERS, MAX_NUMBER_OF_FOOTPRINTS, POINT_COUNT_THRESHOLD, engine)

# Add floor points to building pointcloud
print("Starting floor point adding", datetime.now().strftime("%H:%M:%S"))
gdf_pc = gdf[gdf.geom!=None]
gdf_pc = add_floor_points_to_points_in_gdf(gdf_pc)

# Save raw pointcloud without threshhold or scaling
print("numpy list creation", datetime.now().strftime("%H:%M:%S"))
lidar_numpy_list = list(gdf_pc.geom.apply(convert_multipoint_to_numpy))
# Save building point clouds as npy
print("Starting numpy saving", datetime.now().strftime("%H:%M:%S"))
save_lidar_numpy_list(lidar_numpy_list, gdf_pc, DIR_NPY)

# Save raw information of footprints, epc label, uprn, file mapping

# footprints
print("Starting saving additional data", datetime.now().strftime("%H:%M:%S"))

gdf_footprints = gpd.GeoDataFrame({"if_fp": gdf.id_fp, "geometry": gdf.geom_fp})
gdf_footprints = gdf_footprints.drop_duplicates()
save_path = os.path.join(DIR_AOI_OUTPUT, str('footprints_' + AREA_OF_INTEREST_CODE + ".json"))
gdf_footprints.to_file(save_path, driver="GeoJSON")
# uprn
gdf_uprn = gpd.GeoDataFrame({"uprn": gdf.uprn, "geometry": gdf.geom_uprn})
gdf_uprn = gdf_uprn.drop_duplicates()
save_path = os.path.join(DIR_AOI_OUTPUT, str('uprn_' + AREA_OF_INTEREST_CODE + ".json"))
gdf_uprn.to_file(save_path, driver="GeoJSON")
# epc label
gdf_epc = pd.DataFrame(
    {"id_epc_lmk_key": gdf.id_epc_lmk_key,
     "rating": gdf.energy_rating,
     "efficiency": gdf.energy_efficiency}
)
gdf_epc = gdf_epc.drop_duplicates()
save_path = os.path.join(DIR_AOI_OUTPUT, str('epc_' + AREA_OF_INTEREST_CODE + ".json"))
gdf_epc.to_json(save_path, orient='records')
# label - filename mapping
file_names = file_name_from_polygon_list(list(gdf.geom_fp), file_extension='.npy')
gdf_mapping = pd.DataFrame(
    {"id_fp": gdf.id_fp,
     "uprn": gdf.uprn,
     "id_id_epc_lmk_key": gdf.id_epc_lmk_key,
     "id_query": gdf.id_query,
     "num_p_in_pc": gdf.num_p_in_pc,
     "epc_rating": gdf.energy_rating,
     "epc_efficiency": gdf.energy_efficiency,
     "file_name": file_names}
)
save_path = os.path.join(DIR_AOI_OUTPUT, str('label_filename_mapping_' + AREA_OF_INTEREST_CODE + ".json"))
gdf_mapping.to_json(save_path, orient='index')

# Visualization for evaluation of results

pce_file_names = file_name_from_polygon_list(list(gdf_pc.geom_fp), file_extension=".html")
# Visualize example building pointcloud data
for i, lidar_pc in enumerate(lidar_numpy_list):
    if i <= NUMBER_EXAMPLE_VISUALIZATIONS:
        save_path = os.path.join(DIR_VISUALIZATION, pce_file_names[i])
        visualize_single_3d_point_cloud(
            lidar_pc,
            title=str(i),
            save_path=save_path,
            show=False
        )

# Download aerial image for the building examples
gdf_lat_lon = gdf.to_crs(4326)

img_filenames = file_name_from_polygon_list(list(gdf_pc.geom_fp), file_extension=".png")
for i, building in enumerate(gdf_lat_lon.iloc):
    if i <= NUMBER_EXAMPLE_VISUALIZATIONS:
        cp = building.geom.centroid
        get_aerial_image_lat_lon(
            latitude=cp.y,
            longitude=cp.x,
            image_name=img_filenames[i],
            horizontal_px=512,
            vertical_px=512,
            scale=1,
            zoom=21,
            save_directory=DIR_AERIAL_IMAGES
        )
