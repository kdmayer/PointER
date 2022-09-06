import geopandas as gpd
import numpy as np

import json
import laspy
import os
import pdal
import psycopg2
import time

from geoalchemy2 import Geometry
from sqlalchemy import create_engine

import config as config
from utils.visualization import visualize_single_3d_point_cloud
from utils.utils import normalize_geom, convert_multipoint_to_numpy, gdf_fp_geometries_wkb_to_shape


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

DB_TABLE_NAME_LIDAR = 'uk_lidar_data'
DB_TABLE_NAME_FOOTRPINTS = 'footprints'

###############################################################################
# Configuration
NUMBER_OF_FOOTPRINTS = 10 # define how many footprints should be used for cropping
POINT_COUNT_THRESHOLD = 1000 # define minimum points in pointcloud, smaller pointclouds are dismissed
NUMBER_EXAMPLE_VISUALIZATIONS = 10 # define how many example 3D plots should be created
STANDARD_SRID = 27700 # define the SRID. needs to be same for footprints and lidar data

###############################################################################
# Intialize connection to database
db_connection_url = 'postgresql://' + config.POSTGRES_USER + ':' \
                    + config.POSTGRES_PASSWORD + '@' \
                    + config.POSTGRES_HOST + ':' \
                    + config.POSTGRES_PORT + '/' \
                    + config.POSTGRES_DATABASE

engine = create_engine(db_connection_url, echo=True)

###############################################################################
# Load footprints into database. Existing footprint table is replaced!!!
# load geojson into gdf
files_footprints = os.listdir(DIR_BUILDING_FOOTPRINTS)
files_footprints = [file for file in files_footprints if file[-8:] == '.geojson']

# get all footprints data in directory
gdf_footprint_list = []
for file_footprint in files_footprints:
    file_path_footprint = os.path.join(DIR_BUILDING_FOOTPRINTS, file_footprint)
    gdf_footprint_list.append(gpd.read_file(file_path_footprint))

# append multiple footprints data
gdf_footprints = gdf_footprint_list[0]
for i in np.arange(1, len(gdf_footprint_list)):
    gdf_footprints.append(gdf_footprint_list[i])

gdf_footprints = gdf_footprints.to_crs(STANDARD_SRID)

# write footprints data to database
gdf_footprints.to_postgis(
    DB_TABLE_NAME_FOOTRPINTS,
    engine,
    if_exists='replace',
    index=True,
    index_label='id_fp',
    dtype={'geometry': Geometry(geometry_type='POLYGON', srid=STANDARD_SRID)}
)

###############################################################################
# Load point cloud data into database

# get files in directory
files_uk_lidar = os.listdir(DIR_LAS_FILES)

# check which laz files have not yet been unpacked
laz_files = [file for file in files_uk_lidar if file[-4:] == ".laz"]
las_files = [file for file in files_uk_lidar if file[-4:] == ".las"]
unpacked_files = [laz_file for laz_file in laz_files if not laz_file[:-4] + '.las' in las_files]

# unzip LAZ files, if corresponding LAS file does not exist
for unpacked_file in unpacked_files:
    # unzip laz to las
    in_laz = os.path.join(DIR_LAS_FILES, unpacked_file)
    out_las = os.path.join(DIR_LAS_FILES, unpacked_file[:-4] + '.las')
    las = laspy.read(in_laz)
    las = laspy.convert(las)
    las.write(out_las)

    print('Now loading pointcloud data from las to database. This process can take several minutes')

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
                "capacity": 800
            },
            {
                "type": "writers.pgpointcloud",
                "connection": "host='%s' dbname='%s' user='%s' password='%s' port='%s'" %
                              (config.POSTGRES_HOST, config.POSTGRES_DATABASE,
                               config.POSTGRES_USER, config.POSTGRES_PASSWORD,
                               config.POSTGRES_PORT),
                "schema": "public",
                "table": DB_TABLE_NAME_LIDAR,
                "compression": "dimensional",
                "srid": "27700"
            }
        ]
    }

    pipeline = pdal.Pipeline(json.dumps(las_to_db_pipeline))
    pipeline.execute()

    print('Loading to database finished for tile %s' % out_las)

###############################################################################
# Add geoindex to footprint and lidar tables

# We use psycopg2 for the sql query, because the VACUUM function did not work
# with sqlalchemy (transaction block error)

# define sql queries
sql_query_geoindex_footprints = (
        "CREATE INDEX geoid ON %s USING GIST (geometry);"
        % DB_TABLE_NAME_FOOTRPINTS
)
sql_query_geoindex_footprints_vacuum = (
        "VACUUM ANALYZE %s (geometry)" % DB_TABLE_NAME_FOOTRPINTS
)
sql_query_geoindex_pointclouds = (
        "CREATE INDEX geoid_pa on %s using GIST (Geometry(pa));"
        % DB_TABLE_NAME_LIDAR
)
sql_query_geoindex_pointclouds_vacuum = (
        "VACUUM ANALYZE %s (pa)" % DB_TABLE_NAME_LIDAR
)

# create connection and cursor
connection_psycopg2 = psycopg2.connect(db_connection_url)
connection_psycopg2.autocommit = True
cursor = connection_psycopg2.cursor()

# execute geoindexing footprints
cursor.execute(sql_query_geoindex_footprints)
# execute vacuuming footprints (used to improve geoindex)
cursor.execute(sql_query_geoindex_footprints_vacuum)

# add geoindex to lidar table, only if data was added, otherwise, geoindex already exists
if len(unpacked_files) > 0:
    # execute geoindexing lidar
    cursor.execute(sql_query_geoindex_pointclouds)
    # execute vacuuming lidar (used to improve geoindex)
    cursor.execute(sql_query_geoindex_pointclouds_vacuum)

# commit the transaction
connection_psycopg2.commit()
# close the database communication
connection_psycopg2.close()

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
        select st_buffer(st_transform(fps.geometry, 27700), 10) fp, fps.id_fp, fps.id osm_id 
        from %s fps
        where fps.id_fp < %s
    ),
    patch_unions as (
        select fps.id_fp, pc_union(pc_intersection(pa, fps.fp)) pau
        from %s lp
        inner join footprints fps on pc_intersects(lp.pa, fps.fp) 
        group by fps.id_fp 
    ), 
    building_pc as (
        select 
            id_fp, 
            st_union(geom) geom,
            max(pc_get(p, 'X')) - min(pc_get(p, 'X')) delta_x,
            max(pc_get(p, 'Y')) - min(pc_get(p, 'Y')) delta_y,
            max(pc_get(p, 'Z')) - min(pc_get(p, 'Z')) delta_z,
            min(pc_get(p, 'Z')) z_min
        from (
            select id_fp, pc_explode(pau) p, pc_explode(pau)::geometry geom
            from patch_unions
        ) po
        group by id_fp 
    )
    select 
        bpc.id_fp,
        bpc.geom,
        fps.fp fp_geom,
        fps.osm_id,
        bpc.delta_x,
        bpc.delta_y,
        bpc.delta_z,
        bpc.z_min,
        greatest(bpc.delta_x, bpc.delta_y, bpc.delta_z) scaling_factor,
        st_numgeometries(geom) num_p_in_pc
    from building_pc bpc
    left join footprints fps on bpc.id_fp = fps.id_fp 
    where st_numgeometries(geom) > %s
    """ % (DB_TABLE_NAME_FOOTRPINTS, NUMBER_OF_FOOTPRINTS, DB_TABLE_NAME_LIDAR, POINT_COUNT_THRESHOLD)
)

# start timer
start_time = time.perf_counter()
# actual fetching step
gdf = gpd.GeoDataFrame.from_postgis(sql_query_grouped_points, engine)
# end timer
elapsed_time = time.perf_counter() - start_time
print("Elapsed time: %s s\nTime per footprint %s s"
      % (elapsed_time, elapsed_time / NUMBER_OF_FOOTPRINTS))

# convert fp_geom column from wkb to shape. it is wkb because gpd only loads one geom column from postgis
gdf = gdf_fp_geometries_wkb_to_shape(gdf)

###############################################################################
# Determine scaling factor (max x/y/z of all points)
scaling_factor = np.max(gdf.scaling_factor)

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
for i, lidar_pc in enumerate(lidar_numpy_list):
    npz_file_name = str(int(gdf.iloc[i].fp_geom.centroid.x)) + "_" + \
                    str(int(gdf.iloc[i].fp_geom.centroid.y)) + ".npz"
    npz_file_path = os.path.join(DIR_NPZ, npz_file_name)
    np.savez(npz_file_path, arr=lidar_pc)

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
        title=str(i) + '_normalized',
        save_dir=DIR_VISUALIZATION,
        show=False
    )