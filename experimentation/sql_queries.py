# space to save alternative sql queries

# query to receive building footprint geometries and check if database connection works
sql_test_query = "select *, f.wkb_geometry geom from footprints f"

# query to receive all points in footprints as a row. all point information is fetched. watch out, this could become
# a massive dataframe
NUMBER_OF_FOOTPRINTS = 10
DB_TABLE_NAME = 'uk_lidar_data'

sql_query_all_points = (
    """ with footprints as (
            select st_buffer(st_transform(wkb_geometry, 27700), 3) fp, footprints.ogc_fid id
            from footprints
            where footprints.ogc_fid < %s
        ),
        patch_unions as (
            select fc.id, pc_union(pc_intersection(pa, fc.fp)) pau
            from %s lp
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
    """ % (NUMBER_OF_FOOTPRINTS, DB_TABLE_NAME)
)
