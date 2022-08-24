from sqlalchemy import create_engine
import geopandas as gpd
import config as config


db_connection_url = 'postgresql://' + config.POSTGRES_USER + ':' \
                    + config.POSTGRES_PASSWORD + '@' \
                    + config.POSTGRES_HOST + ':' \
                    + config.POSTGRES_PORT + '/' \
                    + config.POSTGRES_DATABASE

con = create_engine(db_connection_url, echo=True)

num_footprints = 100

sql_test_query = "select *, f.wkb_geometry geom from footprints f"

sql_query_grouped_points = (
    """with footprints as (
            select st_buffer(st_transform(wkb_geometry, 27700), 3) fp, footprints.ogc_fid id
            from footprints
            where footprints.ogc_fid < %s
        ),
        patch_unions as (
            select fc.id, pc_union(pc_intersection(pa, fc.fp)) pau
            from pointcloud_test lp
            inner join footprints fc on pc_intersects(lp.pa, fc.fp) 
            group by fc.id 
        )
        select id, st_union(geom) geom
        from (
            select id, pc_explode(pau) p,  st_transform(st_force2d(pc_explode(pau)::geometry), 4326) geom
            from patch_unions
        ) po
        group by id 
    """ % num_footprints
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


gdf = gpd.GeoDataFrame.from_postgis(sql_query_grouped_points, con)

print('debug point')