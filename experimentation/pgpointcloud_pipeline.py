from sqlalchemy import create_engine

import config as config
import geopandas as gpd
import numpy as np

import time

from utils.visualization import visualize_single_3d_point_cloud
from utils.utils import normalize_geom, _convert_multipoint_to_numpy


db_connection_url = 'postgresql://' + config.POSTGRES_USER + ':' \
                    + config.POSTGRES_PASSWORD + '@' \
                    + config.POSTGRES_HOST + ':' \
                    + config.POSTGRES_PORT + '/' \
                    + config.POSTGRES_DATABASE

con = create_engine(db_connection_url, echo=True)

num_footprints = 10
scaling_factor = 100
random_sample_size = 2000
example_visualizations = 10

sql_test_query = "select *, f.wkb_geometry geom from footprints f"

sql_query_grouped_points = (
    """
    with footprints as (
        select st_buffer(st_transform(wkb_geometry, 27700), 10) fp, footprints.ogc_fid ogc_fid, footprints.id osm_id
        from footprints
        where footprints.ogc_fid < %s
    ),
    patch_unions as (
        select fc.ogc_fid, pc_union(pc_intersection(pa, fc.fp)) pau
        from pointcloud_test lp
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
    """ % (num_footprints, random_sample_size)
)

sql_query_all_points = (
    """ with footprints as (
            select st_buffer(st_transform(wkb_geometry, 27700), 3) fp, footprints.ogc_fid id
            from footprints
            where footprints.ogc_fid < %s
        ),
        patch_unions as (
            select fc.id, pc_union(pc_intersection(pa, fc.fp)) pau
            from pointcloud_test lp
            inner join footprints fc on pc_intersects(lp.pa, fc.fp) 
            group by fc.id 
        ),
        points as (
            select pc_explode(pau) p, id
            from patch_unions
        )
        select *, 
            pc_astext(p) p,
            pc_get(p, 'Intensity') Intensity,
            pc_get(p, 'ReturnNumber') ReturnNumber,
            pc_get(p, 'NumberOfReturns') NumberOfReturns,
            pc_get(p, 'ScanDirectionFlag') ScanDirectionFlag,
            pc_get(p, 'EdgeOfFlightLine') EdgeOfFlightLine,
            pc_get(p, 'Classification') Classification,
            pc_get(p, 'ScanAngleRank') ScanAngleRank,
            pc_get(p, 'UserData') UserData,
            pc_get(p, 'PointSourceId') PointSourceId,
            pc_get(p, 'GpsTime') GpsTime,
            pc_get(p, 'X') X,
            pc_get(p, 'Y') Y,
            pc_get(p, 'Z') Z,
            st_transform(st_force2d(p::geometry), 4326) geom
        from points 
    """ % num_footprints
)

start_time = time.perf_counter()
gdf = gpd.GeoDataFrame.from_postgis(sql_query_grouped_points, con) # query result requires geom column with geometries
elapsed_time = time.perf_counter() - start_time
print("Elapsed time: %s s\nTime per footprint %s s" % (elapsed_time, elapsed_time / num_footprints))

# make sure all building point clouds have enough points (sql query should ensure this)
do_pointclouds_have_enough_points = (np.array([len(g.geoms) for g in gdf.geom]) >= random_sample_size).all()
assert do_pointclouds_have_enough_points==True, 'not all gdf entries have the required amount of points'

# apply normalization function to entire dataframe
lidar_numpy_list = list(gdf.geom.apply(normalize_geom, args=[scaling_factor, random_sample_size]))

# visualize point clouds before and after normalization
for i, lidar_pc in enumerate(lidar_numpy_list):
    # visualize non normalized buildings
    lidar_pc_non_normalized = _convert_multipoint_to_numpy(gdf.iloc[i].geom)
    visualize_single_3d_point_cloud(lidar_pc_non_normalized, title=str(i), save_dir='', show=False)

    # visualize normalized
    visualize_single_3d_point_cloud(lidar_pc, title=str(i) + 'normalized', save_dir='', show=False)

