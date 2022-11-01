import geopandas as gpd
import numpy as np

import json
import laspy
import os

import pandas as pd
import pdal
import psycopg2
import shapely

from geoalchemy2 import Geometry

import config as config

from utils.utils import normalize_geom, gdf_geometries_wkb_to_shape


def load_geojson_footprints_into_database(DIR_BUILDING_FOOTPRINTS, DB_TABLE_NAME_FOOTRPINTS, engine, STANDARD_CRS):
    # load geojson into gdf
    files_footprints = os.listdir(DIR_BUILDING_FOOTPRINTS)
    files_footprints = [file for file in files_footprints if file[-8:] == '.geojson']

    # get all footprints data in directory
    for i, file_footprint in enumerate(files_footprints):
        file_path_footprint = os.path.join(DIR_BUILDING_FOOTPRINTS, file_footprint)
        gdf_footprint = gpd.read_file(file_path_footprint)

        # make sure CRS is correct
        if gdf_footprint.crs != STANDARD_CRS:
            gdf_footprint = gdf_footprint.to_crs(STANDARD_CRS)

        # initialize first geodataframe
        if i == 0:
            gdf_footprints = gdf_footprint
        else:
            gdf_footprints = gdf_footprints.append(gdf_footprint, ignore_index=True)

    # write footprints data to database
    gdf_footprints.to_postgis(
        DB_TABLE_NAME_FOOTRPINTS,
        engine,
        if_exists='replace',
        index=True,
        index_label='id_fp',
        dtype={'geometry': Geometry(geometry_type='POLYGON', srid=STANDARD_CRS)}
    )
    return gdf_footprints


# Load point cloud data into database
def load_laz_pointcloud_into_database(DIR_LAS_FILES, DB_TABLE_NAME_LIDAR):
    # get files in directory
    files_uk_lidar = os.listdir(DIR_LAS_FILES)

    # check which laz files have not yet been unpacked
    import_history_filename = os.path.join(DIR_LAS_FILES, "laz_import_history_do_not_delete.csv")
    laz_file_list = [file for file in files_uk_lidar if file[-4:] == ".laz"]
    # if no history file exists: use all laz files in directory and create history file
    if not os.path.isfile(import_history_filename):
        print(""" no LAZ files have been imported to database so far. 
        if they have, make sure the import history.csv is in the LAZ file directory""")
        import_laz_files = laz_file_list.copy()
        df_new_imports = pd.DataFrame({"imported_files": import_laz_files})
        df_new_imports.to_csv(import_history_filename)
    # if no history file does exist: select only non imported files and update history file
    elif os.path.isfile(import_history_filename):
        df_import_history = pd.read_csv(import_history_filename)
        import_laz_files = [laz_file for laz_file in laz_file_list
                            if not laz_file in df_import_history['imported_files']]
        df_new_imports = pd.DataFrame({"imported_files": import_laz_files})
        df_import_history.append(df_new_imports)
        df_import_history.to_csv(import_history_filename)

    print('Importing pointcloud data from las to database. This process can take several minutes')
    # unzip LAZ files, if corresponding LAS file does not exist
    for i, import_laz_files in enumerate(import_laz_files):
        print('unpacking laz file %s of %s: %s' % (str(i + 1), str(len(import_laz_files)), import_laz_files))
        # unzip laz to las
        in_laz = os.path.join(DIR_LAS_FILES, import_laz_files)
        out_las = os.path.join(DIR_LAS_FILES, import_laz_files[:-4] + '.las')
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
                    "srid": "27700",
                    "overwrite": "false"
                }
            ]
        }

        print('loading laz file %s of %s into database' % (str(i + 1), str(len(import_laz_files))))
        pipeline = pdal.Pipeline(json.dumps(las_to_db_pipeline))
        pipeline.execute()

    print('Loading data into database finished')

    return


def add_geoindex_to_databases(db_connection_url: str, db_table_name_list: list, db_is_pointcloud_table_list: list):
    # Add geoindex to tables while treating lidar tables differently than 2D geom tables
    # Use psycopg2 for the sql query, because the VACUUM function does not work with sqlalchemy
    # (transaction block error)

    for i, table_name in enumerate(db_table_name_list):
        # define sql queries
        idx_name = ('%s_geom_geom_idx' % table_name)
        sql_query_check_geoidx = (
                "SELECT indexname = '%s' FROM pg_indexes WHERE tablename = '%s'"
                % (idx_name, table_name)
        )
        if db_is_pointcloud_table_list[i] == 0:
            # indexing and vacuum query differ slightly for pointcloud db
            sql_query_geoindex = (
                    "CREATE INDEX %s ON %s USING GIST (geom);" % (idx_name, table_name)
            )
            sql_query_vacuum = (
                    "VACUUM ANALYZE %s (geom)" % table_name
            )
        elif db_is_pointcloud_table_list[i] == 1:
            sql_query_geoindex = (
                    "CREATE INDEX %s on %s using GIST (Geometry(pa));" % (idx_name, table_name)
            )
            sql_query_vacuum = (
                    "VACUUM ANALYZE %s (pa)" % table_name
            )

        # create connection and cursor
        connection_psycopg2 = psycopg2.connect(db_connection_url)
        connection_psycopg2.autocommit = True
        cursor = connection_psycopg2.cursor()
        # check if lidar table already contains geo index
        cursor.execute(sql_query_check_geoidx)
        geoindex_exists = np.array(cursor.fetchall()).any()
        # add geoindex only if indext does not yet exist
        if not geoindex_exists:
            print('Creating geoindex on table %s. This process can take several minuts' % table_name)
            # execute geoindexing
            cursor.execute(sql_query_geoindex)
        # execute vacuuming (used to improve geoindex)
        cursor.execute(sql_query_vacuum)
        # commit the transaction
        connection_psycopg2.commit()
        # close the database communication
        connection_psycopg2.close()
    return


def crop_and_fetch_pointclouds_per_building(
        AREA_OF_INTEREST_CODE, BUILDING_BUFFER_METERS, NUMBER_OF_FOOTPRINTS, POINT_COUNT_THRESHOLD, engine):
    # Fetch cropped point clouds from database

    # Query to fetch points within building footprints as multipoint grouped by building.
    # IMPORTANT: query with geopandas requires a geom column in database to create a GeoDataFrame

    # SQL Query explanation:
    # with footprints: defines prepares footprints from footprint table
    # with patch_unions: crops the point clouds and prepares a pointcloud union per building
    # with building_pc: transforms the pointcloud unions into multi points, grouped per building
    # select: fetches the multipoints per building and adds additional information:
    #   - ogc_fid: id of entry in footprint database (1 ... n)
    #   - geom: multipoint of pointcloud cropped by building footprint outline
    #   - num_p_in_pc: number of points in pointcloud
    #   - geom_fp: footprint polygon
    #   - osm_id: OSM id of footprint, prefix is way/ or /relation

    # query is dynamically adapted by the number of requested footprints (num_footprints) as well as the sample size
    # of the pointclouds (POINT_COUNT_THRESHOLD)

    sql_query_grouped_points = (
            """
            -- select area of interest boundary 
            with area_of_interest as (
                select st_transform(geom, 27700) geom
                from local_authority_boundaries lab
                where lab.lad21cd = '%s'
            ),
            footprints as (
                select fps.geom geom_fp, fps.gid id_fp
                from footprints_verisk fps, area_of_interest
                where st_intersects(fps.geom, area_of_interest.geom)
                limit %s
            ),
            fp_buffer as (
                select id_fp, st_buffer(fps.geom_fp, %s) geom_fp
                from footprints fps
            ),
            fp_uprn as (
                select fps.id_fp, fps.geom_fp, u.uprn, (u.geom) geom_uprn
                from footprints fps 
                left join uprn u 
                on st_intersects(fps.geom_fp, u.geom)
            ),
            epc as (
                select *
                from epc e
                where "LOCAL_AUTHORITY" = '%s'
            ),
            fp_uprn_epc as (
                select row_number() over (order by fpu.id_fp) as id_uprn_epc, *
                from fp_uprn fpu
                left join epc e
                on fpu.uprn=e."UPRN" 
            ),
            patch_unions as (
                select fpb.id_fp, pc_union(pc_intersection(pa, fpb.geom_fp)) pau
                from uk_lidar_data lp
                inner join fp_buffer fpb on pc_intersects(lp.pa, fpb.geom_fp) 
                group by fpb.id_fp 
            ),
            building_pc as (
                select 
                    id_fp, 
                    st_union(geom) geom_pc,
                    max(pc_get(p, 'X')) - min(pc_get(p, 'X')) delta_x,
                    max(pc_get(p, 'Y')) - min(pc_get(p, 'Y')) delta_y,
                    max(pc_get(p, 'Z')) - min(pc_get(p, 'Z')) delta_z,
                    min(pc_get(p, 'Z')) z_min
                from (
                    select id_fp, pc_explode(pau) p, pc_explode(pau)::geometry geom
                        from patch_unions
                    ) po
                    group by id_fp 
            ),
            building_pc_fp as (
                select 
                    bpc.id_fp id_fp_bpc,
                    bpc.geom_pc,
                    fps.geom_fp geom_fp_bpc,
                    bpc.delta_x,
                    bpc.delta_y,
                    bpc.delta_z,
                    bpc.z_min,
                    greatest(bpc.delta_x, bpc.delta_y, bpc.delta_z) scaling_factor,
                    st_numgeometries(geom_pc) num_p_in_pc
                from building_pc bpc
                left join footprints fps on bpc.id_fp = fps.id_fp 
                where st_numgeometries(geom_pc) > %s
            ),
            building_pc_fp_epc as (
                select 
                    id_uprn_epc id_query,
                    id_fp,
                    uprn,
                    "LMK_KEY" id_epc_lmk_key,
                    geom_fp,
                    geom_uprn,
                    geom_pc geom,
                    delta_x,
                    delta_y,
                    delta_z,
                    z_min,
                    scaling_factor,
                    num_p_in_pc,
                    "CURRENT_ENERGY_RATING" energy_rating,		
                    "CURRENT_ENERGY_EFFICIENCY" energy_efficiency
                from fp_uprn_epc fps
                left join building_pc_fp bpf 
                on fps.id_fp = bpf.id_fp_bpc
            )
            select distinct *
            from building_pc_fp_epc
            
            """ % (AREA_OF_INTEREST_CODE, NUMBER_OF_FOOTPRINTS, BUILDING_BUFFER_METERS,
                   AREA_OF_INTEREST_CODE, POINT_COUNT_THRESHOLD)
    )

    # actual fetching step
    gdf = gpd.GeoDataFrame.from_postgis(sql_query_grouped_points, engine)

    # convert geom_fp and geom_uprn column from wkb to shape.
    # those columns are wkb because gpd only loads one geom column from postgis
    gdf = gdf_geometries_wkb_to_shape(gdf)

    return gdf


def add_floor_points_to_points_in_gdf(gdf):
    pointcloud_with_floor_list = []
    for i, row in enumerate(gdf.iloc):
        new_pointcloud = add_floor_points_to_pointcloud(row.geom_fp, row.geom, row.z_min)
        pointcloud_with_floor_list.append(new_pointcloud)
        if i % 100 == 0:
            print('processing pointcloud %s out of %s' % (i, len(gdf)))
    gdf = gdf.assign(geom=pointcloud_with_floor_list)
    return gdf


def add_floor_points_to_pointcloud(building_footprint: shapely.geometry.Polygon,
                                   pointcloud: shapely.geometry.MultiPoint,
                                   z_min):
    # Grid spacing in meters
    resolution = 0.5
    lonmin, latmin, lonmax, latmax = building_footprint.bounds

    # construct rectangle of points
    x, y = np.round(np.meshgrid(np.arange(lonmin, lonmax, resolution), np.arange(latmin, latmax, resolution)), 4)
    points = list(zip(x.flatten(), y.flatten()))

    # validate each point falls inside shapes and add minimum z-vale of lidar point cloud as floor level
    valid_points = [(point[0], point[1], z_min) for point in points if
                    building_footprint.contains(shapely.geometry.Point(point))]

    footprint_multipoint = shapely.geometry.MultiPoint(valid_points)
    new_multipoint = shapely.ops.unary_union([pointcloud, footprint_multipoint])
    return new_multipoint


###############################################################################
def get_scaling_factor(gdf):
    # Determine scaling factor (max delta_x/delta_y/delta_z of all points)
    scaling_factor = np.max(gdf.scaling_factor)
    return scaling_factor


###############################################################################
def pointcloud_gdf_to_numpy(gdf, scaling_factor, POINT_COUNT_THRESHOLD):
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
    return lidar_numpy_list


###############################################################################
# Save building point clouds as npy
def save_lidar_numpy_list(lidar_numpy_list, gdf, dir_npy):
    # IMPORTANT: lidar_numpy_list order must be the same as gdf to ensure correct naming of .npy
    for i, lidar_pc in enumerate(lidar_numpy_list):
        npy_file_name = str(gdf.iloc[i].geom_fp.centroid.x) + "_" + \
                        str(gdf.iloc[i].geom_fp.centroid.y) + ".npy"
        npy_file_path = os.path.join(dir_npy, npy_file_name)
        with open(npy_file_path, 'wb') as f:
            np.save(f, arr=lidar_pc)
    return