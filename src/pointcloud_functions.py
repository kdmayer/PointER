import pdal
import psycopg2
import shapely
import json
import laspy
import os

import config as config
import geopandas as gpd
import pandas as pd
import numpy as np

from geoalchemy2 import Geometry
from utils.utils import normalize_geom, gdf_geometries_wkb_to_shape, file_name_from_polygon_list

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

    laz_files = [file for file in files_uk_lidar if file[-4:] == ".laz"]
    las_files = [file for file in files_uk_lidar if file[-4:] == ".las"]

    laz_file_list = [laz_file for laz_file in laz_files if not laz_file[:-4] + '.las' in las_files]

    import_laz_files = laz_file_list
    #    # check which laz files have not yet been unpacked
    #    import_history_filename = os.path.join(DIR_LAS_FILES, "laz_import_history_do_not_delete.csv")
    #    # if no history file exists: use all laz files in directory and create history file
    #    if not os.path.isfile(import_history_filename):
    #        print("""no LAZ files have been imported to database so far. if they have, make sure the import history.csv
    #        is in the LAZ file directory""")
    #        import_laz_files = laz_file_list.copy()
    #        df_new_imports = pd.DataFrame({"imported_files": import_laz_files})
    #        df_new_imports.to_csv(import_history_filename)
    #    # if no history file does exist: select only non imported files and update history file
    #    elif os.path.isfile(import_history_filename):
    #        print("Some of the files in the directory have already been imported to DB (see %s). Only non imported files "
    #              "will be uploaded to database" %import_history_filename)

    #        df_import_history = pd.read_csv(import_history_filename)
    #        imported_files_list = list(df_import_history['imported_files'])
    #        import_laz_files = [laz_file for laz_file in laz_file_list
    #                            if not laz_file in imported_files_list]
    #        df_new_imports = pd.DataFrame({"imported_files": import_laz_files})
    #        df_import_history.append(df_new_imports)
    #        df_import_history.to_csv(import_history_filename)

    # unzip LAZ files, if corresponding LAS file does not exist
    print('Importing pointcloud data from laz to database. This process can take several minutes')
    for i, import_laz_file in enumerate(import_laz_files):
        print('unpacking laz file %s of %s: %s' % (str(i + 1), str(len(import_laz_files)), import_laz_file))
        # unzip laz to las (not necessary anymore - LAZ is directly imported to db)
        in_laz = os.path.join(DIR_LAS_FILES, import_laz_file)
        out_las = os.path.join(DIR_LAS_FILES, import_laz_file[:-4] + '.las')
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
                    "table": DB_TABLE_NAME_LIDAR,
                    "compression": "dimensional",
                    "srid": "27700",
                    "overwrite": "false"
                }
            ]
        }

        print('importing laz file %s of %s into database: %s' % (
            str(i + 1), str(len(import_laz_files)), str(import_laz_file)))
        pipeline = pdal.Pipeline(json.dumps(las_to_db_pipeline))
        pipeline.execute()

    print('Importing data into database finished')

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


def crop_and_fetch_pointclouds_per_building(FP_NUM_START, FP_NUM_END, AREA_OF_INTEREST_CODE, BUILDING_BUFFER_METERS,
        NUMBER_OF_FOOTPRINTS, POINT_COUNT_THRESHOLD, TABLE_NAME_UPRN, TABLE_NAME_EPC, TABLE_NAME_LIDAR, engine):
    # Fetch cropped point clouds from database

    # Query to fetch points within building footprints as multipoint grouped by building.
    # IMPORTANT: query with geopandas requires a geom column in database to create a GeoDataFrame

    # SQL Query explanation:
    # todo: adapt description for final version
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
            with footprints as (
                select geom_fp, id_fp
                from "%s" aoi
                where aoi.id_fp_chunks > %s and aoi.id_fp_chunks <= %s
                limit %s
            ),
            fp_buffer as (
                select id_fp, st_buffer(fps.geom_fp, %s) geom_fp
                from footprints fps
            ),
            fp_uprn as (
                select fps.id_fp, fps.geom_fp, u.uprn, (u.geom) geom_uprn
                from footprints fps 
                left join %s u 
                on st_intersects(fps.geom_fp, u.geom)
            ),
            epc as (
                select *
                from %s e
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
                from %s lp
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

            """ % (AREA_OF_INTEREST_CODE, FP_NUM_START, FP_NUM_END, NUMBER_OF_FOOTPRINTS, BUILDING_BUFFER_METERS,
                   TABLE_NAME_UPRN, TABLE_NAME_EPC, AREA_OF_INTEREST_CODE, TABLE_NAME_LIDAR, POINT_COUNT_THRESHOLD)
    )

    # actual fetching step
    gdf = gpd.GeoDataFrame.from_postgis(sql_query_grouped_points, engine)

    # convert geom_fp and geom_uprn column from wkb to shape.
    # those columns are wkb because gpd only loads one geom column from postgis
    gdf = gdf_geometries_wkb_to_shape(gdf)

    return gdf


def create_footprints_in_area_materialized_view(
        db_connection_url: str, AREA_OF_INTEREST_CODE: str, NUMBER_OF_FOOTPRINTS: str,
        TABLE_NAME_LOCAL_AUTHORITY_BOUNDARY, TABLE_NAME_FOOTPRINTS):
    sql_query_get_existing_materialized_views = (
        """select matviewname as view_name from pg_matviews where matviewname = '%s'""" % AREA_OF_INTEREST_CODE
    )
    sql_query_drop_existing_materialized_view = (
            """drop materialized view "%s";""" % AREA_OF_INTEREST_CODE
    )
    sql_query_footprint_materialzed_view = (
            """
            create materialized view "%s" as (
                with area_of_interest as (
                    select st_transform(geom, 27700) geom
                    from %s lab
                    where lab.lad21cd = '%s'
                ),
                footprints as (
                    select row_number() over (order by fps.gid) as id_fp_chunks, fps.geom geom_fp, fps.gid id_fp
                    from %s fps, area_of_interest
                    where st_intersects(fps.geom, area_of_interest.geom)
                    limit %s
                )
                select *
                from footprints
            )
    """ % (AREA_OF_INTEREST_CODE, TABLE_NAME_LOCAL_AUTHORITY_BOUNDARY, AREA_OF_INTEREST_CODE,
           TABLE_NAME_FOOTPRINTS, NUMBER_OF_FOOTPRINTS)
    )
    sql_query_get_number_of_footprints = (
        """select count(*) from "%s" """ % AREA_OF_INTEREST_CODE
    )


    # create connection and cursor
    connection_psycopg2 = psycopg2.connect(db_connection_url)
    cursor = connection_psycopg2.cursor()
    # check if materialized view already exists
    cursor.execute(sql_query_get_existing_materialized_views)
    existing_view = np.array(cursor.fetchall())
    # drop existing materialized view
    if len(existing_view) == 1:
        cursor.execute(sql_query_drop_existing_materialized_view)
    # create new materialized view with footpints in aera of interest
    cursor.execute(sql_query_footprint_materialzed_view)
    # get number of footprints in aera of interest
    cursor.execute(sql_query_get_number_of_footprints)
    num_footprints = cursor.fetchall()[0][0]
    # commit the transaction
    connection_psycopg2.commit()
    # close the database communication
    connection_psycopg2.close()
    return num_footprints


def add_floor_points_to_points_in_gdf(gdf):
    pointcloud_with_floor_list = []
    for i, row in enumerate(gdf.iloc):
        new_pointcloud = add_floor_points_to_pointcloud(row.geom_fp, row.geom, row.z_min)
        pointcloud_with_floor_list.append(new_pointcloud)
        if i % 1000 == 0:
            print('processing pointcloud %s out of %s' % (i, len(gdf)))
    gdf = gdf.assign(geom=pointcloud_with_floor_list)
    print('list added to gdf')
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


def get_scaling_factor(gdf):
    # Determine scaling factor (max delta_x/delta_y/delta_z of all points)
    scaling_factor = np.max(gdf.scaling_factor)
    return scaling_factor


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


def save_raw_input_information(n_iteration, gdf: gpd.GeoDataFrame, DIR_AOI_OUTPUT: str, AOI_CODE: str):
    # saves information required for creating building point clouds except point cloud data itself
    # footprints
    gdf_footprints = gpd.GeoDataFrame({"id_fp": gdf.id_fp, "geometry": gdf.geom_fp})
    gdf_footprints = gdf_footprints.drop_duplicates()
    save_path = os.path.join(
        DIR_AOI_OUTPUT, 'footprints', str('footprints_' + AOI_CODE + '_' + str(int(n_iteration)) + ".json"))
    gdf_footprints.to_file(save_path, driver="GeoJSON")
    # uprn
    gdf_uprn = gpd.GeoDataFrame({"uprn": gdf.uprn, "geometry": gdf.geom_uprn})
    gdf_uprn = gdf_uprn.drop_duplicates()
    save_path = os.path.join(DIR_AOI_OUTPUT, 'uprn', str('uprn_' + AOI_CODE + '_' + str(int(n_iteration)) + ".json"))
    gdf_uprn.to_file(save_path, driver="GeoJSON")
    # epc label
    gdf_epc = pd.DataFrame(
        {"id_epc_lmk_key": gdf.id_epc_lmk_key,
         "rating": gdf.energy_rating,
         "efficiency": gdf.energy_efficiency}
    )
    gdf_epc = gdf_epc.drop_duplicates()
    save_path = os.path.join(DIR_AOI_OUTPUT, 'epc', str('epc_' + AOI_CODE + '_' + str(int(n_iteration)) + ".json"))
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
    save_path = os.path.join(DIR_AOI_OUTPUT, 'filename_mapping',
                             str('label_filename_mapping_' + AOI_CODE + '_' + str(int(n_iteration)) + ".json")
    )
    gdf_mapping.to_json(save_path, orient='index')
    return


def production_metrics_simple(gdf_fm: gpd.GeoDataFrame, save_path: str, aoi_code: str):
    # gdf_fm: geodataframe with file mapping information
    # calculate
    num_footprints = len(gdf_fm.id_fp.unique())
    num_footprints_pcs = len(gdf_fm[gdf_fm.num_p_in_pc.notna()].id_fp.unique())
    num_footprints_uprn = len(gdf_fm[gdf_fm.uprn.notna()].id_fp.unique())
    num_footprints_uprn_epc = len(gdf_fm[gdf_fm.epc_efficiency.notna()].id_fp.unique())
    num_footprints_full_info = len(gdf_fm.dropna().id_fp.unique())
    # save to dictionary
    production_metrics = {
        'footprints_all': num_footprints,
        'footprints_w_pointclouds': num_footprints_pcs,
        'footprints_w_uprn': num_footprints_uprn,
        'footprints_w_uprn_epc': num_footprints_uprn_epc,
        'footprints_full_info': num_footprints_full_info
    }
    # print information
    metric_str = ''
    for metric in production_metrics.keys():
        relative_metric = str(np.round(production_metrics[metric]/production_metrics['footprints_all']*100, 2))
        metric_str += str('number of ' + metric + ': ' + str(production_metrics[metric]) +
                          ' (%s'%relative_metric + ' %) \n')
    print(metric_str)
    # save
    file_path = os.path.join(save_path, str('production_metrics_' + str(aoi_code) +' .json'))
    with open(file_path, 'w') as f:
        json.dump(production_metrics, f)
    return


def case_specific_json_loader(file_path: str, case: str):
    if case == 'footprints' or case == 'uprn':
        gdf = gpd.read_file(file_path, driver="GeoJSON")
    elif case == 'epc':
        gdf = pd.read_json(file_path, orient='records')
    elif case == 'filename_mapping':
        gdf = pd.read_json(file_path, orient='index')
    else:
        print('this case is not considered, yet. check code!')
    return gdf


def case_specific_json_saver(gdf: gpd.GeoDataFrame, file_path: str, case: str):
    if case == 'footprints' or case == 'uprn':
        gdf.to_file(file_path, driver="GeoJSON")
    elif case == 'epc':
        gdf.to_json(file_path, orient='records')
    elif case == 'filename_mapping':
        gdf = gdf.reset_index()
        gdf = gdf.drop("index", axis=1)
        gdf.to_json(file_path, orient='index')
    else:
        print('this case is not considered, yet. check code!')
    return


def stitch_raw_input_information(dir_outputs: str, area_of_interest_code: str, SUB_FOLDER_LIST: list):
    DIR_AOI_OUTPUT = os.path.join(dir_outputs, area_of_interest_code)
    for subdir in SUB_FOLDER_LIST:
        if subdir != 'npy_raw':
            dir_path = os.path.join(DIR_AOI_OUTPUT, subdir)
            jsons_in_dir = [file for file in os.listdir(dir_path) if file[-5:] == '.json']
            # open jsons and append all data in directory
            for i, json_in_dir in enumerate(jsons_in_dir):
                file_path = os.path.join(dir_path, json_in_dir)
                gdf_snippet = case_specific_json_loader(file_path, subdir)
                if i == 0:
                    gdf = gdf_snippet.copy()
                else:
                    gdf = gdf.append(gdf_snippet)
            # save stitched file
            save_path = os.path.join(DIR_AOI_OUTPUT, str(str(subdir) + '_' + str(area_of_interest_code) + '.json'))
            case_specific_json_saver(gdf, save_path, subdir)
    return


def output_folder_setup(dir_outputs: str, area_of_interest_code: str, SUB_FOLDER_LIST: list):
    # create outputs folder
    if not os.path.isdir(dir_outputs):
        os.mkdir(dir_outputs)
    # create area of interest folder
    DIR_AOI_OUTPUT = os.path.join(dir_outputs, area_of_interest_code)
    if os.path.isdir(DIR_AOI_OUTPUT):
        print('output for this area of interest already exists. delete or choose other area code')
    else:
        os.mkdir(DIR_AOI_OUTPUT)
        # create sub-folders for pointcloud data and meta data
        for subdir in SUB_FOLDER_LIST:
            dir_path = os.path.join(DIR_AOI_OUTPUT, subdir)
            if not os.path.isdir(dir_path): os.mkdir(dir_path)
    return DIR_AOI_OUTPUT



