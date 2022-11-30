# todo: remove the surpression of warnings
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Import python packages
import sys
from sqlalchemy import create_engine
from datetime import datetime

# Import functions from own .py scripts
from src.pointcloud_functions import *
from utils.utils import convert_multipoint_to_numpy, check_directory_paths, file_name_from_polygon_list
from utils.visualization import visualize_single_3d_point_cloud
from utils.aerial_image import get_aerial_image_lat_lon

# Add parent folder to path, so that notebook can find .py scripts
DIR_BASE = os.path.abspath('..')
if DIR_BASE not in sys.path:
    sys.path.append(DIR_BASE)

######################   Configuration   #####################################
# Define pointcloud parameters
# UK local authority boundary code to specify area of interest (AOI)
AREA_OF_INTEREST_CODE = 'E06000014'
# buffer around building footprint in meters
BUILDING_BUFFER_METERS = 0.5
# define how many footprints should be created. Use "None" to use all footprints in AOI
MAX_NUMBER_OF_FOOTPRINTS = None
# number of footprints per query (size of data requires processing in chunks)
NUM_FOOTPRINTS_CHUNK_SIZE = 500
# define minimum points in pointcloud, smaller pointclouds are dismissed
POINT_COUNT_THRESHOLD = 100
# define how many example 3D plots should be created
NUMBER_EXAMPLE_VISUALIZATIONS = 20
# define if google aerial images should be downloaded for evaluation purposes.
# Make sure to add a google key in the config file if this is set to True!
ENABLE_AERIAL_IMAGE_DOWNLOAD = False

# Define project base directory and paths
DIR_ASSETS = os.path.join(DIR_BASE, 'assets')
DIR_LAZ_FILES = os.path.join(DIR_ASSETS, "uk_lidar_data")
DIR_EPC = os.path.join(DIR_ASSETS, "epc")
DIR_VISUALIZATION = os.path.join(DIR_ASSETS, "example_pointclouds")
DIR_AERIAL_IMAGES = os.path.join(DIR_ASSETS, "aerial_image_examples")

# Create a new output folder for the defined area of interest
DIR_OUTPUTS = os.path.join('/home/vagrant/data_share', 'outputs')
SUB_FOLDER_LIST = ['npy_raw', 'footprints', 'uprn', 'epc', 'filename_mapping']
DIR_AOI_OUTPUT = output_folder_setup(DIR_OUTPUTS, AREA_OF_INTEREST_CODE, SUB_FOLDER_LIST)

# Check that all required directories exist
check_directory_paths([DIR_ASSETS, DIR_OUTPUTS, DIR_LAZ_FILES, DIR_VISUALIZATION, DIR_AERIAL_IMAGES, DIR_AOI_OUTPUT])

# Define database table names
DB_TABLE_NAME_LIDAR = 'uk_lidar_data'
DB_TABLE_NAME_FOOTPRINTS = 'footprints_verisk'
DB_TABLE_NAME_UPRN = 'uprn'
DB_TABLE_NAME_EPC = 'epc'
DB_TABLE_NAME_AREA_OF_INTEREST = 'local_authority_boundaries'

# Intialize connection to database
DB_CONNECTION_URL = config.DATABASE_URL
engine = create_engine(DB_CONNECTION_URL, echo=False)

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

# # Load EPC data into database
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

# Create materialized view of footprints in area of interest (required for processing in chunks)
num_footprints = create_footprints_in_area_materialized_view(
    DB_CONNECTION_URL, AREA_OF_INTEREST_CODE, MAX_NUMBER_OF_FOOTPRINTS, DB_TABLE_NAME_AREA_OF_INTEREST,
    DB_TABLE_NAME_FOOTPRINTS
)

print("Starting point cloud cropping", datetime.now().strftime("%H:%M:%S"))
# processing the cropping in chunks
num_iterations = np.ceil(num_footprints / NUM_FOOTPRINTS_CHUNK_SIZE)
# initialize loop's variables, because they are deleted at beginning of every loop to avoid memory overflow
gdf = gpd.GeoDataFrame()
gdf_pc = gpd.GeoDataFrame()
lidar_numpy_list = []
for n_iteration in np.arange(0, num_iterations):
    # delete gdf manually to avoid memory overflow
    del gdf, gdf_pc, lidar_numpy_list

    print("Prcoessing footprints - chunk %s out of %s - " % (n_iteration, num_iterations),
          datetime.now().strftime("%H:%M:%S"))
    fp_num_start = n_iteration * NUM_FOOTPRINTS_CHUNK_SIZE
    fp_num_end = (n_iteration + 1) * NUM_FOOTPRINTS_CHUNK_SIZE

    # Fetch cropped point clouds from database
    gdf = crop_and_fetch_pointclouds_per_building(
        fp_num_start, fp_num_end, AREA_OF_INTEREST_CODE, BUILDING_BUFFER_METERS, MAX_NUMBER_OF_FOOTPRINTS,
        POINT_COUNT_THRESHOLD, DB_TABLE_NAME_UPRN, DB_TABLE_NAME_EPC, DB_TABLE_NAME_LIDAR, engine
    )
    # Add floor points to building pointcloud
    print("Floor point adding - chunk %s out of %s - " % (n_iteration, num_iterations),
          datetime.now().strftime("%H:%M:%S"))
    gdf_pc = gdf[gdf.geom != None].copy()
    gdf_pc = add_floor_points_to_points_in_gdf(gdf_pc)

    # Save raw pointcloud without threshhold or scaling
    print("Numpy list creation - chunk %s out of %s - " % (n_iteration, num_iterations),
          datetime.now().strftime("%H:%M:%S"))
    lidar_numpy_list = list(gdf_pc.geom.apply(convert_multipoint_to_numpy))
    # Save building point clouds as npy
    print("Numpy saving - chunk %s out of %s - " % (n_iteration, num_iterations), datetime.now().strftime("%H:%M:%S"))
    dir_npy = os.path.join(DIR_AOI_OUTPUT, 'npy_raw')
    save_lidar_numpy_list(lidar_numpy_list, gdf_pc, dir_npy)

    # Save raw information of footprints, epc label, uprn, file mapping
    print("Save additional data - chunk %s out of %s - " % (n_iteration, num_iterations),
          datetime.now().strftime("%H:%M:%S"))
    save_raw_input_information(n_iteration, gdf, DIR_AOI_OUTPUT, AREA_OF_INTEREST_CODE)

# stitch all raw input information jsons to create one result json
stitch_raw_input_information(DIR_OUTPUTS, AREA_OF_INTEREST_CODE, SUB_FOLDER_LIST)

# calculate simple production metrics for point cloud production in area of interest
file_path = os.path.join(DIR_AOI_OUTPUT, str('filename_mapping_' + str(AREA_OF_INTEREST_CODE) + '.json'))
# load mapping geodataframe
gdf_fm = case_specific_json_loader(file_path, 'filename_mapping')
# calculate metrics
production_metrics_simple(gdf_fm, DIR_AOI_OUTPUT, AREA_OF_INTEREST_CODE)

# Visualization for evaluation of results
# Visualize example building pointcloud data
pce_file_names = file_name_from_polygon_list(list(gdf_pc.geom_fp), file_extension=".html")
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
if ENABLE_AERIAL_IMAGE_DOWNLOAD:
    gdf_fp_lat_lon = gpd.GeoDataFrame(
        {"id_fp": gdf_pc.id_fp,
         "geometry": gdf_pc.geom_fp}
    )
    gdf_fp_lat_lon.crs = 27700
    gdf_fp_lat_lon = gdf_fp_lat_lon.to_crs(4326)

    img_filenames = file_name_from_polygon_list(list(gdf_fp_lat_lon.geometry), file_extension=".png")
    for i, building in enumerate(gdf_fp_lat_lon.iloc):
        if i <= NUMBER_EXAMPLE_VISUALIZATIONS:
            cp = building.geometry.centroid
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
