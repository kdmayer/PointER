import geopandas as gpd
import numpy as np

import os
import shapely
import laspy

from utils import utils as utils
import utils.visualization as visualization
from experimentation.pdal_pipeline import run_pdal_pipeline


# Define project base directory
DIR_BASE = os.getcwd()
DIR_ASSETS = os.path.join(os.path.dirname(DIR_BASE), 'assets')
assert DIR_ASSETS.split("\\")[-1] == 'assets', "You are not in the assets directory"

# Configuration
LAS_FILE_PATH = os.path.join(DIR_ASSETS, "SP3025_P_10700_20190328_20190328.las")
POINT_COUNT_THRESHOLD = 1000

# Run subsample test
# test = utils.subsample_las(LAS_FILE_PATH)
# print(test)

# Import footprint polygons
FOOTPRINTS_FILE_PATH = os.path.join(DIR_ASSETS, "chipping_norton_building_footprints.geojson")
osm_footprints = gpd.read_file(FOOTPRINTS_FILE_PATH)

# Reproject OSM footprints to EPSG:27700, if necessary
osm_footprints = osm_footprints.to_crs("EPSG:27700")
#osm_footprints.to_file("coventry_building_footprints.geojson", driver='GeoJSON')

# Buffer polygons a bit to capture the building footprint better
osm_footprints["geometry"] = osm_footprints["geometry"].buffer(1)

footprint_list = osm_footprints['geometry'].tolist()

# Select only polygons which are within the LiDAR tile and save their WKT string
lidar_bounding_box = utils.create_tile_bounding_box(LAS_FILE_PATH)
polys = [elem.wkt for elem in footprint_list if isinstance(elem, shapely.geometry.polygon.Polygon) and lidar_bounding_box.contains(elem.centroid)]
print(f"Number of relevant polygons: {len(polys)}")

# crop LiDAR data in footprints using pdal
sample_size = 10
run_pdal_pipeline(footprint_list=polys, las_file_path=LAS_FILE_PATH, random_sample_size=sample_size)
print("Process ran: %s seconds \n That is ~ %s per building footprint", (stop_time, int(stop_time/sample_size)))

# load and postprocess cropped LiDAR point cloud examples
point_cloud_examples = []
point_cloud_filenames = []

for file_path in os.listdir(os.getcwd()):

    # All PDAL-based output files start with "cropped"
    if file_path.startswith("cropped"):

        las_point_cloud = laspy.read(file_path)
        point_count = len(las_point_cloud.points)

        if point_count < POINT_COUNT_THRESHOLD:
            os.remove(file_path)

        else:

            numpy_point_cloud = utils._convert_las_to_numpy(las_point_cloud)
            numpy_point_cloud = utils._sample_random_points(x=numpy_point_cloud, random_sample_size=POINT_COUNT_THRESHOLD)
            numpy_point_cloud = numpy_point_cloud[np.newaxis, ...]

            point_cloud_examples.append(numpy_point_cloud)
            point_cloud_filenames.append(file_path)

point_cloud_examples = np.concatenate(point_cloud_examples, axis=0)
point_cloud_examples.shape

# visualize cropped point cloud examples
visualization.visualize_3d_array(point_cloud_examples, point_cloud_filenames, example_ID=3)