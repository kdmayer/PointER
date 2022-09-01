import geopandas as gpd
from geoalchemy2 import Geometry, WKTElement
import numpy as np

import json
import laspy
import os
import pdal
import time

from sqlalchemy import create_engine

import config as config
from utils.visualization import visualize_single_3d_point_cloud
from utils.utils import normalize_geom, convert_multipoint_to_numpy

###############################################################################
# Define project base directory and paths
DIR_BASE = os.getcwd()
DIR_ASSETS = os.path.join(os.path.dirname(DIR_BASE), 'assets')
assert DIR_ASSETS.split("\\")[-1] == 'assets', \
    "You are not in the assets directory"

DIR_BUILDING_FOOTPRINTS = os.path.join(DIR_ASSETS, "aoi")
DIR_LAS_FILES = os.path.join(DIR_ASSETS, "uk_lidar_data")
DIR_NPZ = os.path.join(DIR_ASSETS, "pointcloud_npz")
DIR_VISUALIZATION = os.path.join(DIR_ASSETS, "example_pointclouds")

###############################################################################
# Configuration
NUMBER_OF_FOOTPRINTS = 10
POINT_COUNT_THRESHOLD = 1000
NUMBER_EXAMPLE_VISUALIZATIONS = 10
STANDARD_SRID = 27700

###############################################################################
# Intialize connection to database
db_connection_url = 'postgresql://' + config.POSTGRES_USER + ':' \
                    + config.POSTGRES_PASSWORD + '@' \
                    + config.POSTGRES_HOST + ':' \
                    + config.POSTGRES_PORT + '/' \
                    + config.POSTGRES_DATABASE

engine = create_engine(db_connection_url, echo=True)

###############################################################################
# # Load footprints into database
# # todo: make sure that footprints are not duplicated in database
# # todo: add unique row id to footprint database (formerly ogc_fid)
# # load geojson into gdf
# files_footprints = os.listdir(DIR_BUILDING_FOOTPRINTS)
# files_footprints = [file for file in files_footprints if file[-8:] == '.geojson']
#
# gdf_footprint_list = []
# for file_footprint in files_footprints:
#     file_path_footprint = os.path.join(DIR_BUILDING_FOOTPRINTS, file_footprint)
#     gdf_footprint_list.append(gpd.read_file(file_path_footprint))
#
# gdf_footprints = gdf_footprint_list[0]
# for i in np.arange(1, len(gdf_footprint_list)):
#     gdf_footprints.append(gdf_footprint_list[i])
#
# gdf_footprints = gdf_footprints.to_crs(STANDARD_SRID)
#
# gdf_footprints.to_postgis(
#     'footprints',
#     engine,
#     if_exists='append',
#     index=False,
#     dtype={'geometry': Geometry(geometry_type='POLYGON', srid=STANDARD_SRID)}
# )

###############################################################################
# Load point cloud data into database

# get files in directory
files_uk_lidar = os.listdir(DIR_LAS_FILES)

# check which laz files have not yet been unpacked
laz_files = [file for file in files_uk_lidar if file[-4:] == ".laz"]
las_files = [file for file in files_uk_lidar if file[-4:] == ".las"]
unpacked_files = [laz_file for laz_file in laz_files if laz_file[:-4] + '.las' in las_files]

# unzip LAZ files, if corresponding LAS file does not exist
for unpacked_file in unpacked_files:
    # unzip laz to las
    in_laz = os.path.join(DIR_LAS_FILES, unpacked_file)
    out_las = os.path.join(DIR_LAS_FILES, unpacked_file[:-4] + '.las')
    las = laspy.read(in_laz)
    las = laspy.convert(las)
    las.write(out_las)

    # load las files into database
    las_to_db_pipeline = {
        "pipeline": [
            {
                "type": "readers.las",
                "filename": out_las,
                "spatialreference": "EPSG:27700"
            },
            {
                "type": "filters.chipper",
                "capacity": 400
            },
            {
                "type": "writers.pgpointcloud",
                "connection": "host='%s' dbname='%s' user='%s' password='%s' port='%s'" %
                              (config.POSTGRES_HOST, config.POSTGRES_DATABASE,
                               config.POSTGRES_USER, config.POSTGRES_PASSWORD,
                               config.POSTGRES_PORT),
                "schema": "public",
                "table": "uk_lidar_data",
                "compression": "dimensional",
                "srid": "27700"
            }
        ]
    }
    # todo: fix pipeline to load las data into database from python
    file_path_pdal_las_to_db = os.path.join(DIR_BASE, "pdal_las_to_db.json")
    with open(file_path_pdal_las_to_db, "w") as f:
        json.dump(las_to_db_pipeline, f)
    os.system("pdal pipeline --input %s" %file_path_pdal_las_to_db)

###############################################################################
# Determine scaling factor (max x/y/z of all points)
# todo: determine scaling factor based on lidar points in database
scaling_factor = 100

###############################################################################
# Fetch cropped point clouds from database

# query to fetch points within building footprints as multipoint grouped by building.
# IMPORTANT: query with geopandas requires a geom column in database to create a GeoDataFrame

# SQL Query explanation:
# with footprints: defines prepares footprints from footprint table
# with patch_unions: crops the point clouds and prepares a pointcloud union per building
# with building_pc: transforms the pointcloud unions into multi points, grouped per building
# select: fetches the multipoints per building and adds additional information:
#   - ogc_fid: id of entry in footprint database (1 ... n)
#   - geom: multipoint of pointcloud cropped by building footprint outline
#   - num_p_in_pc: number of points in pointcloud
#   - fp_geom: footprint polygon
#   - osm_id: OSM id of footprint, prefix is way/ or /relation

# query is dynamically adapted by the number of requested footprints (num_footprints) as well as the sample size
# of the pointclouds (POINT_COUNT_THRESHOLD)

sql_query_grouped_points = (
        """
    with footprints as (
        select st_buffer(st_transform(geometry, 27700), 10) fp, footprints.ogc_fid ogc_fid, footprints.id osm_id 
        from footprints
        where footprints.ogc_fid < %s
    ),
    patch_unions as (
        select fc.ogc_fid, pc_union(pc_intersection(pa, fc.fp)) pau
        from uk_lidar_data lp
        inner join footprints fc on pc_intersects(lp.pa, fc.fp) 
        group by fc.ogc_fid 
    ), 
    building_pc as (
        select ogc_fid, st_union(geom) geom
        from (
            select ogc_fid, pc_explode(pau) p, pc_explode(pau)::geometry geom
            from patch_unions
        ) po
        group by ogc_fid 
    )
    select bpc.ogc_fid, bpc.geom, st_numgeometries(geom) num_p_in_pc, fp.fp fp_geom, fp.osm_id
    from building_pc bpc
    left join footprints fp on bpc.ogc_fid = fp.ogc_fid 
    where st_numgeometries(geom) > %s
    """ % (NUMBER_OF_FOOTPRINTS, POINT_COUNT_THRESHOLD)
)

# start timer
start_time = time.perf_counter()
# actual fetching step
gdf = gpd.GeoDataFrame.from_postgis(sql_query_grouped_points, engine)
# end timer
elapsed_time = time.perf_counter() - start_time
print("Elapsed time: %s s\nTime per footprint %s s"
      % (elapsed_time, elapsed_time / NUMBER_OF_FOOTPRINTS))

###############################################################################
# Convert fetched building point clouds to numpy
# make sure all building point clouds have enough points,
# although sql query should already ensure this
do_pointclouds_have_enough_points = \
    (np.array([len(g.geoms) for g in gdf.geom]) >= POINT_COUNT_THRESHOLD).all()
assert do_pointclouds_have_enough_points, \
    'not all gdf entries have the required amount of points'

# apply normalization function to entire dataframe
lidar_numpy_list = list(
    gdf.geom.apply(
        normalize_geom,
        args=[scaling_factor, POINT_COUNT_THRESHOLD])
)

###############################################################################
# Save building point clouds as npz
# todo: code the saving to npz function

###############################################################################
# Visualize example data before and after normalization
for i, lidar_pc in enumerate(lidar_numpy_list):
    # visualize non normalized buildings
    lidar_pc_non_normalized = convert_multipoint_to_numpy(gdf.iloc[i].geom)
    visualize_single_3d_point_cloud(
        lidar_pc_non_normalized,
        title=str(i),
        save_dir=DIR_VISUALIZATION,
        show=False
    )
    # visualize normalized
    visualize_single_3d_point_cloud(
        lidar_pc,
        title=str(i) + 'normalized',
        save_dir=DIR_VISUALIZATION,
        show=False
    )
