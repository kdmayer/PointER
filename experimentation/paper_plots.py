import os
import sys
import pickle

from shapely.geometry import box
from sqlalchemy import create_engine

# # Load output area rural urban classification data into database
DIR_BASE = os.path.abspath('..')
if DIR_BASE not in sys.path:
    sys.path.append(DIR_BASE)

from utils.visualization import *
from src.pointcloud_functions import case_specific_json_loader
import config

########################################################################################################################
#
# The following code generates the figures used in the paper that is published together with the dataset
#
########################################################################################################################

### Path definitions
# path to the results directory of point cloud generation script
DIR_OUTPUTS = os.path.join(DIR_BASE, 'outputs')
# outputs including footprints (version that is not published along paper, because of license)
DIR_OUTPUTS_ALL = os.path.join('D:\\', 'outputs_all')
# path to directory where plots are saved
DIR_PAPER_PLOTS = os.path.join(DIR_BASE, 'assets', 'paper_plots')


########################################################################################################################
# Definition of functions prepare the data and plot the figures
########################################################################################################################

### Visualize local authority districts (LAD)
def local_authority_plot(DIR_OUTPUTS, DIR_PAPER_PLOTS):
    file_path = os.path.join(DIR_BASE, "archive", "gdf_LAD.pkl")
    # only do database query, if intermediate pickle file has not yet been created, to speed up debugging
    if not os.path.isfile(file_path):
        # Intialize connection to database
        db_connection_url = config.DATABASE_URL
        engine = create_engine(db_connection_url, echo=False)
        # Query LAD data
        sql_LAD = "SELECT lad21cd, lad21nm, geom FROM local_authority_boundaries lad"
        gdf_LAD = gpd.GeoDataFrame.from_postgis(sql_LAD, engine)

        with open(file_path, "wb") as f:
            pickle.dump(gdf_LAD, f)
    else:
        with open(file_path, "rb") as f:
            gdf_LAD = pickle.load(f)

    # create country boundaries
    gdf_countries = gpd.GeoDataFrame({
        'name': ["England", "Scotland", "Wales"],
        'geometry': [gdf_LAD.geometry[[lad[0] == "E" for lad in gdf_LAD.lad21cd]].unary_union,
                     gdf_LAD.geometry[[lad[0] == "S" for lad in gdf_LAD.lad21cd]].unary_union,
                     gdf_LAD.geometry[[lad[0] == "W" for lad in gdf_LAD.lad21cd]].unary_union]
    })

    print("created countries gdf")
    # Define LAD ids that should be highlighted
    LAD_ids = os.listdir(DIR_OUTPUTS)
    LAD_ids = [lad for lad in LAD_ids if lad != '.gitkeep' and lad != 'example_aoi']

    save_path = os.path.join(DIR_PAPER_PLOTS, 'LAD_selected.png')
    visualize_local_authority_districts(gdf_LAD, gdf_countries, LAD_ids, save_path)

    return


def point_cloud_examples_plot(DIR_OUTPUTS, DIR_PAPER_PLOTS):
    # define list of 9 images that should be plotted - 3 okay, 3 edge case and 3 low quality point clouds
    pc_filenames = [
        "246948.78976353028_54582.104618081765",
        "407794.9737427337_296532.7641717685",
        "433853.78865251393_278803.57210055826",
        "450586.32330317964_207896.18002823117",
        "340813.70719685976_389079.85148259345",
        "449464.8349280443_333042.0673046965",
        "507057.26790191786_134159.87110376408",
        "510936.22000000003_381457.105",
        "352120.5055914023_528731.969464525"
    ]
    pc_filenames = [pc_filename + ".npy" for pc_filename in pc_filenames]

    nrows = 3
    ncols = 3
    angles = [30, 45, 30, 0, 115, 90, 30, 30, -30]
    save_path = os.path.join(DIR_PAPER_PLOTS, "point_cloud_examples.svg")
    point_cloud_grid_visualization(
        DIR_OUTPUTS, pc_filenames, ncols, nrows, angles, save_path)

    return


def buildings_less_than_100_points(dir_outputs, dir_paper_plots, example_AOI_1, example_AOI_2, center_point_example_1,
                                   center_point_example_2, section_size_m):
    """ Function that plots two sections that show buildings above and below point cloud threshold
    IMPORTANT: Assumes DIR_OUTPUTS which includes footprint data (as opposed to cleaned-up paper dataset) """

    # create bounding boxes for sections that should be visualized
    gdf_cps = gpd.GeoDataFrame({'ids': [0, 1], 'geometry': [center_point_example_1, center_point_example_2]})
    gdf_cps.crs = 4326
    gdf_cps = gdf_cps.to_crs(27700)
    bboxes = [box(cp.x - section_size_m / 2,
                  cp.y - section_size_m / 2,
                  cp.x + section_size_m / 2,
                  cp.y + section_size_m / 2
                  ) for cp in gdf_cps.geometry]
    gdf_bboxes = gpd.GeoDataFrame({
        'ids': [0, 1],
        'geometry': bboxes
    })
    gdf_bboxes.crs = 27700

    # load data and create GeoDataframes of footprints and num_p_in_pc
    file_path = os.path.join(DIR_BASE, "archive", "gdf_buildings_less_than_100_points.pkl")
    if not os.path.isfile(file_path):

        filepath_footprints = os.path.join(
            dir_outputs, example_AOI_1, str('final_result_verisk_uprn_' + example_AOI_1 + '.geojson'))
        gdf_fp = case_specific_json_loader(filepath_footprints, 'footprints')
        gdf_fp_1 = gpd.GeoDataFrame(
            {'id_fp': gdf_fp.id_fp, 'num_p_in_pc': gdf_fp.num_p_in_pc, 'geometry': gdf_fp.geometry})
        gdf_fp_1.crs = 27700

        filepath_footprints = os.path.join(
            dir_outputs, example_AOI_2, str('final_result_verisk_uprn_' + example_AOI_2 + '.geojson'))
        gdf_fp = case_specific_json_loader(filepath_footprints, 'footprints')
        gdf_fp_2 = gpd.GeoDataFrame(
            {'id_fp': gdf_fp.id_fp, 'num_p_in_pc': gdf_fp.num_p_in_pc, 'geometry': gdf_fp.geometry})
        gdf_fp_2.crs = 27700

        # filter buildings within sections
        gdf_fp_1 = gpd.sjoin(gdf_fp_1, gdf_bboxes, how='left')
        gdf_fp_1 = gdf_fp_1[gdf_fp_1.index_right.notna()]
        gdf_fp_2 = gpd.sjoin(gdf_fp_2, gdf_bboxes, how='left')
        gdf_fp_2 = gdf_fp_2[gdf_fp_2.index_right.notna()]

        with open(file_path, "wb") as f:
            pickle.dump([gdf_fp_1, gdf_fp_2], f)
    else:
        with open(file_path, "rb") as f:
            [gdf_fp_1, gdf_fp_2] = pickle.load(f)

    # visualize buildings
    save_path = os.path.join(dir_paper_plots, "point_threshold_per_building.svg")
    visualize_point_threshold_per_building(gdf_fp_1, gdf_fp_2, save_path)

    return


def method_plot_visualization(dir_outputs, dir_paper_plots):
    '''
    This function plots several figures used for the paper's method figure.
    Note, that the bounding box for the extract of building is currently hard coded in the sql queries below.
    '''

    def get_point_data(engine, bounding_box_string: str):
        sql_query = """-- select points in bounding box
            with bbox as (
                select st_transform(st_setsrid('%s'::geometry, 4326), 27700) geometry
            ),
            patch_unions_in_bbox as (
                select pa
                from bbox, uk_lidar_data uld
                where pc_intersects(uld.pa, bbox.geometry)
            ),
            bbox_pc as (
                select 
                    geom geom_pc,
                    pc_get(p, 'X') x,
                    pc_get(p, 'Y') y,
                    pc_get(p, 'Z') z,
                    st_setsrid(st_makepoint(pc_get(p, 'X'), pc_get(p, 'Y')), 27700) geom_p
                from (
                    select pc_explode(pa) p, pc_explode(pa)::geometry geom
                        from patch_unions_in_bbox
                    ) po
            )
            select *, st_transform(geom_p, 4326) geom
            from bbox_pc
        """ % (bounding_box_string)

        gdf = gpd.GeoDataFrame.from_postgis(sql_query, engine)

        return gdf

    def get_geom_data(engine, bounding_box_string: str, db_table_name):
        sql_query = """-- select geometry data in bounding box
            with bbox as (
                select st_transform(st_setsrid('%s'::geometry, 4326), 27700) geometry
            ),
            footprints as (
                select *, st_transform(geom, 4326) 
                from bbox, %s dt 
                where st_intersects(bbox.geometry, dt.geom)
            )
            select *
            from footprints
        """ % (bounding_box_string, db_table_name)

        gdf = gpd.GeoDataFrame.from_postgis(sql_query, engine)

        return gdf

    def footprints_in_AOI(engine, aoi_code):
        sql_query = """
            with area_of_interest as (
                select st_transform(geom, 27700) geom
                from local_authority_boundaries lab
                where lab.lad21cd = '%s'
            ),
            footprints as (
                select 
                    row_number() over (order by fps.gid) as id_fp_chunks, 
                    fps.geom geom, 
                    fps.gid id_fp,
                    aoi.geom geom_aoi
                from footprints_verisk fps, area_of_interest aoi
                where st_intersects(fps.geom, aoi.geom)
            )
            select *
            from footprints
        """ % (aoi_code)

        gdf = gpd.GeoDataFrame.from_postgis(sql_query, engine)

        return gdf

    # define AOI Code
    BOUNDING_BOX_STRING = 'POLYGON ((-1.083835927313378 53.95357692232674,' \
                          '-1.083835927313378 53.95495794790006,' \
                          '-1.0861105526756154 53.95495794790006,' \
                          '-1.0861105526756154 53.95357692232674,' \
                          '-1.083835927313378 53.95357692232674))'
    AREA_OF_INTEREST_CODE = 'E06000014'

    FILEPATH_MAPPING = os.path.join(dir_outputs, AREA_OF_INTEREST_CODE,
                                    str('filename_mapping_' + AREA_OF_INTEREST_CODE + '.json'))
    gdf_mapping = case_specific_json_loader(FILEPATH_MAPPING, 'filename_mapping')

    # speed up data acquisition for debugging by saving results as pickle
    file_path_gdfs = os.path.join(DIR_BASE, "archive", "method_plot_gdfs.pkl")
    if os.path.isfile(file_path_gdfs):
        with open(file_path_gdfs, "rb") as f:
            [gdf_lidar_points, gdf_footprints, gdf_uprn, gdf_oa, gdf_lad, gdf_footprints_in_AOI] = pickle.load(f)
    else:
        # Intialize connection to database
        db_connection_url = config.DATABASE_URL
        engine = create_engine(db_connection_url, echo=False)

        gdf_lidar_points = get_point_data(engine, BOUNDING_BOX_STRING)
        gdf_lidar_points = gdf_lidar_points.to_crs(27700)
        gdf_footprints = get_geom_data(engine, BOUNDING_BOX_STRING, db_table_name='footprints_verisk')
        gdf_uprn = get_geom_data(engine, BOUNDING_BOX_STRING, db_table_name='uprn')
        gdf_oa = get_geom_data(engine, BOUNDING_BOX_STRING, db_table_name='output_area_boundaries')
        gdf_lad = get_geom_data(engine, BOUNDING_BOX_STRING, db_table_name='local_authority_boundaries')
        gdf_footprints_in_AOI = footprints_in_AOI(engine, aoi_code=AREA_OF_INTEREST_CODE)
        with open(file_path_gdfs, "wb") as f:
            pickle.dump([gdf_lidar_points, gdf_footprints, gdf_uprn, gdf_oa, gdf_lad, gdf_footprints_in_AOI], f)

    # 1 plot footprints in aoi
    save_path = os.path.join(dir_paper_plots, "method_plot_1_footprints_in_aoi.png")
    visualize_footprints_in_AOI(gdf_footprints_in_AOI, gdf_lad, save_path, include_legend=False)

    # 2 footprints with buffer
    save_path = os.path.join(dir_paper_plots, "method_plot_2_footprints_buffer.png")
    visualize_footprints_with_buffer(gdf_footprints, save_path, include_legend=False)

    # 3 points in point cloud
    gdf_footprints.geom = gdf_footprints.buffer(0.5)
    gdf_fp_p_in_pc = gpd.GeoDataFrame(gdf_footprints.set_index("gid").join(gdf_mapping.set_index("id_fp"), how="left"))
    gdf_fp_p_in_pc = gdf_fp_p_in_pc.drop(["uprn", "id_id_epc_lmk_key", "id_query", "epc_efficiency", "epc_rating"],
                                         axis=1)
    gdf_fp_p_in_pc = gdf_fp_p_in_pc.drop_duplicates()
    gdf_fp_p_in_pc = gdf_fp_p_in_pc.set_geometry("geom")

    save_path = os.path.join(dir_paper_plots, "method_plot_3_points_in_footprint.png")
    visualize_points_in_footprint(gdf_lidar_points, gdf_fp_p_in_pc, save_path, include_legend=False)

    # 4 fp with uprn
    gdf_fp_uprn = gdf_footprints.copy()
    gdf_fp_uprn = gdf_fp_uprn.drop([col for col in gdf_footprints.columns if col not in ['geom', "gid"]], axis=1)
    gdf_fp_uprn = gpd.GeoDataFrame(gdf_fp_uprn.set_index("gid").join(gdf_mapping.set_index("id_fp"), how="left"))
    gdf_fp_uprn.insert(0, "id_fp", gdf_fp_uprn.index)
    gdf_fp_uprn_count = gdf_fp_uprn.drop([col for col in gdf_fp_uprn.columns if col not in ['id_fp', "uprn"]], axis=1)
    uprn_count = gdf_fp_uprn_count.groupby('id_fp').count()
    uprn_count = gpd.GeoDataFrame(uprn_count.uprn.rename('uprn_count'))
    gdf_fp_uprn_count = uprn_count.join(gdf_fp_uprn.set_index('id_fp'))

    save_path = os.path.join(dir_paper_plots, "method_plot_4_uprn_per_footprint.png")
    visualize_uprn_or_epc_in_footprints(gdf_fp_uprn_count, case='uprn', save_path=save_path, include_legend=False)

    # 5 footprints with epc
    gdf_fp_epc = gdf_footprints.copy()
    gdf_fp_epc = gdf_fp_epc.drop([col for col in gdf_footprints.columns if col not in ['geom', "gid"]], axis=1)
    gdf_fp_epc = gpd.GeoDataFrame(gdf_fp_epc.set_index("gid").join(gdf_mapping.set_index("id_fp"), how="left"))
    gdf_fp_epc.insert(0, "id_fp", gdf_fp_epc.index)
    gdf_fp_epc_count = gdf_fp_epc.drop([col for col in gdf_fp_epc.columns if col not in ['id_fp', "id_id_epc_lmk_key"]],
                                       axis=1)
    epc_count = gdf_fp_epc_count.groupby('id_fp').count()
    epc_count = gpd.GeoDataFrame(epc_count.id_id_epc_lmk_key.rename('epc_count'))
    gdf_fp_epc_count = epc_count.join(gdf_fp_epc.set_index('id_fp'))

    save_path = os.path.join(dir_paper_plots, "method_plot_5_epc_per_footprint.png")
    visualize_uprn_or_epc_in_footprints(gdf_fp_epc_count, case='epc', save_path=save_path, include_legend=False)

    return


########################################################################################################################
# Main: Calling the functions for the paper plots
########################################################################################################################
# 1) Plot of local authority districts (figure 3)
local_authority_plot(DIR_OUTPUTS, DIR_PAPER_PLOTS)

# 2) Plot of example visualizations used for methods figure (figure  4)
method_plot_visualization(DIR_OUTPUTS, DIR_PAPER_PLOTS)

# 3) Plot of building point cloud examples of different quality (figure 5)
point_cloud_examples_plot(DIR_OUTPUTS, DIR_PAPER_PLOTS)

# 4) Plot to visualize buildings with less than 100 points in Westminster and Coventry (figure 6)
buildings_less_than_100_points(
    dir_outputs=DIR_OUTPUTS_ALL,
    dir_paper_plots=DIR_PAPER_PLOTS,
    example_AOI_1='E09000033',
    example_AOI_2='E08000026',
    center_point_example_1=Point(-0.20136563461604043, 51.52985357621988),  # center point coordinates in CRS 4326
    center_point_example_2=Point(-1.5369260397633102, 52.43090630276185),  # center point coordinates in CRS 4326
    section_size_m=500)


print("done")
