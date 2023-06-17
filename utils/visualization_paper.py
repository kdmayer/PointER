from shapely.geometry import Point
from matplotlib.lines import Line2D

import contextily as cx
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.colors as colors
import numpy as np

import os

from utils.utils import point_cloud_xyz


def point_cloud_grid_visualization(dir_point_clouds, pc_file_names: list = None, ncols: int = 1, nrows: int = 1,
                                   angles: list = None, save_path: str = ''):
    # Define paths to point cloud files
    # EITHER sample random number of point clouds
    if pc_file_names is None:
        pc_file_names = os.listdir(dir_point_clouds)
        random_pcs = np.random.choice(pc_file_names, int(ncols * nrows * 2))
        df = pd.DataFrame({'file_names': random_pcs})
        df = df.drop_duplicates()
        pc_file_names = list(df['file_names'].iloc[0:(ncols * nrows)])
        dirs_point_clouds = [dir_point_clouds for dir in np.arange(0, (ncols * nrows))]
    # OR find the paths of given point clouds in subdirectories
    else:
        # find files in folder directory of multiple folders
        sub_directories = os.listdir(dir_point_clouds)
        dirs_point_clouds = ["" for dir in np.arange(0, (ncols * nrows))]
        for i, file_name in enumerate(pc_file_names):
            count = 0
            file_found = False
            while not file_found and count < len(sub_directories):
                file_path = os.path.join(dir_point_clouds, sub_directories[count], 'npy_raw', file_name)
                file_found = os.path.isfile(file_path)
                count += 1
            if file_found:
                dirs_point_clouds[i] = os.path.join(dir_point_clouds, sub_directories[count-1], 'npy_raw')
            else:
                print('no directory found for file: ' + file_name)

    # Define grid layout
    height_ratio_list = [n for n in np.repeat([1 / nrows], nrows)]
    width_ratio_list = [n for n in np.repeat([1 / ncols], ncols)]

    fig = plt.figure(constrained_layout=True, figsize=(14.7 * 0.3937, 15 * 0.3937))
    fig.tight_layout()

    spec = gridspec.GridSpec(ncols=ncols,
                             nrows=nrows,
                             figure=fig,
                             height_ratios=height_ratio_list,
                             width_ratios=width_ratio_list)
    # define default angles as 45
    if angles is None:
        angles = [45 for i in np.arange(0, (ncols * nrows))]

    axes = []
    for j in np.arange(0, nrows):
        for i in np.arange(0, ncols):
            ax = fig.add_subplot(spec[j, i], projection='3d')
            ax.xaxis.set_ticks([])
            ax.yaxis.set_ticks([])
            ax.zaxis.set_ticks([])
            axes.append(ax)

    # plot image, ground truth and prediction
    fig_count = 0
    for nrow in np.arange(0, nrows):
        for ncol in np.arange(0, ncols):
            pc_file_name = pc_file_names[fig_count]
            dir_point_clouds = dirs_point_clouds[fig_count]
            fig_count += 1
            pc_file_path = os.path.join(dir_point_clouds, pc_file_name)
            point_cloud_array = np.load(pc_file_path)
            # normalize pc array for visualization
            for i in np.arange(0, 3):
                point_cloud_array[:, i] = (point_cloud_array[:, i] - point_cloud_array[:, i].min())

            x, y, z = point_cloud_xyz(point_cloud_array)
            axes[nrow*nrows + ncol].scatter(x, y, z, c=z, s=3, cmap='viridis', marker='o',  alpha=0.6)
            axes[nrow*nrows + ncol].view_init(-27, angles[nrow*nrows + ncol])
    #
    # class_list = list(label_classes) + ['background']
    # values = np.arange(0, len(class_list))
    # colors = [TUM_CI_colors.sem_seg_cmap(value) for value in values]
    # # create a patch (proxy artist) for every color
    # patches = [mpatches.Patch(color=colors[i], label=class_list[i]) for i in range(len(values))]
    fig.tight_layout(pad=0)
    # lax.legend(handles=patches, loc='center', bbox_to_anchor=(0.5, 0.65), ncol=5)

    plt.savefig(save_path, format='svg', dpi=300, bbox_inches='tight')

    return


def visualize_local_authority_districts(gdf_LAD: gpd.GeoDataFrame, gdf_countries: gpd.GeoDataFrame, LAD_ids: list,
                                        save_path: str):
    ''' function that plots local authority district boundaries and country boundaries for paper '''
    fig = plt.figure(constrained_layout=True, figsize=(get_image_size('squared_large')))
    ax = fig.add_subplot()
    ax.xaxis.set_ticks([])
    ax.yaxis.set_ticks([])
    # set y_lim, so that england covers most of the figure
    ax.set_ylim(-10000, 700000)

    gdf_LAD_in = gdf_LAD[[lad in LAD_ids for lad in gdf_LAD.lad21cd]]
    gdf_LAD_out = gdf_LAD[[lad not in LAD_ids for lad in gdf_LAD.lad21cd]]

    # plot country boundaries
    gdf_countries.plot(ax=ax, color='None', edgecolor='black', alpha=1)

    # plot LADs
    gdf_LAD_out.plot(ax=ax, color='gray', edgecolor='darkgreen', alpha=0.2)
    gdf_LAD_in.plot(ax=ax, color='darkgreen', alpha=0.9, edgecolor='darkgreen')

    # save figure
    fig.savefig(save_path, format=save_path[-3:], dpi=500)
    return


def visualize_point_threshold_per_building(gdf_fps_1: gpd.GeoDataFrame, gdf_fps_2: gpd.GeoDataFrame,
                                           save_path, section_size: int = 400):
    # remove duplicate data
    gdf_fps_1 = gdf_fps_1.drop_duplicates()
    gdf_fps_2 = gdf_fps_2.drop_duplicates()

    # define font
    plt.rcParams["font.family"] = "Calibri"
    plt.rcParams["font.size"] = "9"

    # define point color limits
    VMIN = 100
    VMAX = 500

    # initialize figure
    fig = plt.figure(constrained_layout=True, figsize=(14.7 * 0.3937, 8 * 0.3937))

    # define figure layout
    spec = gridspec.GridSpec(ncols=2,
                             nrows=2,
                             figure=fig,
                             height_ratios=[0.95, 0.05],
                             width_ratios=[0.5, 0.5])

    ax1 = fig.add_subplot(spec[0, 0])
    ax2 = fig.add_subplot(spec[0, 1])
    ax3 = fig.add_subplot(spec[1, 0])
    ax4 = fig.add_subplot(spec[1, 1])

    # remove axis ticks
    ax3.axis('off')
    ax1.xaxis.set_ticks([])
    ax1.yaxis.set_ticks([])
    ax2.xaxis.set_ticks([])
    ax2.yaxis.set_ticks([])
    ax3.xaxis.set_ticks([])
    ax3.yaxis.set_ticks([])
    ax4.xaxis.set_ticks([])
    ax4.yaxis.set_ticks([])

    # split footprints into footprints with more and less than threshold number of points
    gdf_fps_1_over_threshold = gdf_fps_1[gdf_fps_1.num_p_in_pc.notna()]
    gdf_fps_1_under_threshold = gdf_fps_1[gdf_fps_1.num_p_in_pc.isna()]
    gdf_fps_2_over_threshold = gdf_fps_2[gdf_fps_2.num_p_in_pc.notna()]
    gdf_fps_2_under_threshold = gdf_fps_2[gdf_fps_2.num_p_in_pc.isna()]

    # plot footprints
    gdf_fps_1_under_threshold.plot(ax=ax1, alpha=0.7, color=[115/255, 0, 42/255])
    gdf_fps_1_over_threshold.plot(ax=ax1, column="num_p_in_pc", alpha=0.7, cmap='viridis_r', vmin=VMIN, vmax=VMAX)

    gdf_fps_2_under_threshold.plot(ax=ax2, alpha=0.7, color=[115/255, 0, 42/255])
    gdf_fps_2_over_threshold.plot(ax=ax2, column="num_p_in_pc", alpha=0.7, cmap='viridis_r', vmin=VMIN, vmax=VMAX)

    # define x and y limits
    bounds_1 = gdf_fps_1.unary_union.bounds
    bounds_2 = gdf_fps_2.unary_union.bounds

    center_point_1 = Point(np.mean([bounds_1[0], bounds_1[2]]), np.mean([bounds_1[1], bounds_1[3]]))
    center_point_2 = Point(np.mean([bounds_2[0], bounds_2[2]]), np.mean([bounds_2[1], bounds_2[3]]))

    ax1.set_xlim([center_point_1.x - section_size/2, center_point_1.x + section_size/2])
    ax1.set_ylim([center_point_1.y - section_size/2, center_point_1.y + section_size/2])
    ax2.set_xlim([center_point_2.x - section_size/2, center_point_2.x + section_size/2])
    ax2.set_ylim([center_point_2.y - section_size/2, center_point_2.y + section_size/2])

    # add open street base map
    cx.add_basemap(ax1, crs=27700, source=cx.providers.OpenStreetMap.Mapnik)
    cx.add_basemap(ax2, crs=27700, source=cx.providers.OpenStreetMap.Mapnik)

    # # create the colorbar
    norm = colors.Normalize(vmin=VMIN, vmax=VMAX)
    cbar = plt.cm.ScalarMappable(norm=norm, cmap='viridis_r')
    ax_cbar = fig.colorbar(cbar, cax=ax4, orientation='horizontal')
    ax_cbar.set_label('points per footprint')

    # patch
    patch = mpatches.Patch(color=[115/255, 0, 42/255], label="less than 100 points")
    # font = font_manager.FontProperties(family='Calibri', style='normal', size=9)
    ax3.legend(handles=[patch], loc='upper center', ncol=1)  # , prop=font)

    # save figure
    fig.savefig(save_path, format=save_path[-3:], dpi=300)
    return


def visualize_footprints_in_AOI(gdf_footprints_in_AOI, gdf_lad, save_path, include_legend=True):
    # define font
    plt.rcParams["font.family"] = "Calibri"
    plt.rcParams["font.size"] = "9"

    # initialize figure
    fig = plt.figure(constrained_layout=True, figsize=(7 * 0.3937, 7 * 0.3937))

    if include_legend:
        # define figure layout
        spec = gridspec.GridSpec(ncols=2,
                                 nrows=2,
                                 figure=fig,
                                 height_ratios=[0.95, 0.05],
                                 width_ratios=[0.5, 0.5])

        ax1 = fig.add_subplot(spec[0, :])
        ax2 = fig.add_subplot(spec[1, 0])
        ax3 = fig.add_subplot(spec[1, 1])


        ax2.axis('off')
        ax3.axis('off')
    else:
        ax1 = fig.add_subplot()

    # remove axis
    ax1.xaxis.set_ticks([])
    ax1.yaxis.set_ticks([])

    # plot footprints and AOI boundary (LAD boundary)
    gdf_footprints_in_AOI.plot(ax=ax1, color='darkgreen', alpha=0.9)
    gdf_lad.plot(ax=ax1, color='gray', edgecolor='black', alpha=0.2)

    if include_legend:
        # add patches as legend
        patch1 = mpatches.Patch(color='gray', alpha=0.2, label="LAD boundary")
        patch2 = mpatches.Patch(color='darkgreen', label="Footprints")
        ax2.legend(handles=[patch1], loc='upper center', ncol=1)  # , prop=font)
        ax3.legend(handles=[patch2], loc='upper center', ncol=1)  # , prop=font)

    fig.savefig(save_path, format=save_path[-3:], dpi=300)

    return


def visualize_footprints_with_buffer(gdf_footprints, save_path, section_size=150, include_legend=True):
    # define font
    plt.rcParams["font.family"] = "Calibri"
    plt.rcParams["font.size"] = "9"

    # initialize figure
    fig = plt.figure(constrained_layout=True, figsize=(7 * 0.3937, 7 * 0.3937))

    if include_legend:
        # define figure layout
        spec = gridspec.GridSpec(ncols=2,
                                 nrows=2,
                                 figure=fig,
                                 height_ratios=[0.95, 0.05],
                                 width_ratios=[0.5, 0.5])

        ax1 = fig.add_subplot(spec[0, :])
        ax2 = fig.add_subplot(spec[1, 0])
        ax3 = fig.add_subplot(spec[1, 1])

        ax2.axis('off')
        ax3.axis('off')
    else:
        ax1 = fig.add_subplot()

    # remove axis ticks
    ax1.xaxis.set_ticks([])
    ax1.yaxis.set_ticks([])

    # define x and y limits
    bounds_1 = gdf_footprints.unary_union.bounds
    center_point_1 = Point(np.mean([bounds_1[0], bounds_1[2]]), np.mean([bounds_1[1], bounds_1[3]]))
    ax1.set_xlim([center_point_1.x - section_size/2, center_point_1.x + section_size/2])
    ax1.set_ylim([center_point_1.y - section_size/2, center_point_1.y + section_size/2])


    # plot footprints and AOI boundary (LAD boundary)
    gdf_footprints.buffer(0.5).plot(ax=ax1, alpha=1, color='none', edgecolor='black')
    gdf_footprints.plot(ax=ax1, alpha=0.7, color='darkgreen')

    if include_legend:
        # add patches as legend
        patch1 = mpatches.Patch(color='darkgreen', edgecolor='none', alpha=0.7, label="Footprints")
        patch2 = mpatches.Patch(facecolor="none", edgecolor='black', alpha=1, label="Buffer")
        ax2.legend(handles=[patch1], loc='upper center', ncol=1)  # , prop=font)
        ax3.legend(handles=[patch2], loc='upper center', ncol=1)  # , prop=font)

    # save
    fig.savefig(save_path, format=save_path[-3:], dpi=300)
    return


def visualize_points_in_footprint(gdf_lidar_points, gdf_fp_p_in_pc, save_path, section_size=150, include_legend=True):
    # define font
    plt.rcParams["font.family"] = "Calibri"
    plt.rcParams["font.size"] = "9"

    # initialize figure
    fig = plt.figure(constrained_layout=True, figsize=(7 * 0.3937, 7 * 0.3937))

    if include_legend:
        # define figure layout
        spec = gridspec.GridSpec(ncols=2,
                                 nrows=3,
                                 figure=fig,
                                 height_ratios=[0.90, 0.05, 0.05],
                                 width_ratios=[0.6, 0.4])

        ax1 = fig.add_subplot(spec[0, :])
        ax2 = fig.add_subplot(spec[1, 0])
        ax3 = fig.add_subplot(spec[1, 1])
        ax4 = fig.add_subplot(spec[2, 0])
        ax5 = fig.add_subplot(spec[2, 1])

        ax2.axis('off')
        ax3.axis('off')
        ax4.axis('off')
        ax5.axis('off')
    else:
        ax1 = fig.add_subplot()

    # remove axis ticks
    ax1.xaxis.set_ticks([])
    ax1.yaxis.set_ticks([])

    # define x and y limits
    bounds_1 = gdf_fp_p_in_pc.unary_union.bounds
    center_point_1 = Point(np.mean([bounds_1[0], bounds_1[2]]), np.mean([bounds_1[1], bounds_1[3]]))
    ax1.set_xlim([center_point_1.x - section_size/2, center_point_1.x + section_size/2])
    ax1.set_ylim([center_point_1.y - section_size/2, center_point_1.y + section_size/2])

    # calculate subsets of gdfs
    gdf_p_in_fp = gpd.sjoin(gdf_lidar_points, gdf_fp_p_in_pc, how='left', op='intersects')
    gdf_p_in_fp = gdf_p_in_fp.set_geometry("geom")
    gdf_p_inside_fp = gdf_p_in_fp[gdf_p_in_fp.index_right.notna()]
    gdf_p_outside_fp = gdf_p_in_fp[gdf_p_in_fp.index_right.isna()]
    # fp_threshold = gdf_p_inside_fp.groupby('index_right').count()
    gdf_fp_enough_points = gdf_fp_p_in_pc[gdf_fp_p_in_pc.num_p_in_pc.notna()]
    gdf_fp_too_few_points = gdf_fp_p_in_pc[gdf_fp_p_in_pc.num_p_in_pc.isna()]

    # plot points and footprints
    gdf_fp_enough_points.plot(ax=ax1, alpha=0.7, color='darkgreen', edgecolor='darkgreen')
    gdf_fp_too_few_points.plot(ax=ax1, alpha=0.7, color=[115/255, 0, 42/255], edgecolor=[115/255, 0, 42/255])

    gdf_p_inside_fp.plot(ax=ax1, markersize=0.005, color='black', alpha=0.4)
    gdf_p_outside_fp.plot(ax=ax1, markersize=0.002, color='orange', alpha=0.5)

    if include_legend:
        # add patches as legend
        patch1 = mpatches.Patch(color='darkgreen', edgecolor='darkgreen', alpha=0.7, label="FP >= 100 points")
        patch2 = mpatches.Patch(color=[115/255, 0, 42/255], edgecolor=[115/255, 0, 42/255], alpha=0.7, label="FP < 100 points")
        circle1 = Line2D([0], [0], marker='o', color='w', label='inside FP', markerfacecolor='black', alpha=0.8, markersize=5)
        circle2 = Line2D([0], [0], marker='o', color='w', label='outside FP', markerfacecolor='orange', alpha=0.8, markersize=5)
        # patch2 = mpatches.Patch(facecolor='black', alpha=0.8, label="point in footprint")
        # patch4 = mpatches.Circle(facecolor='orange', alpha=0.8, label="point outside footprint")
        ax2.legend(handles=[patch1], loc='upper center', ncol=1)  # , prop=font)
        ax3.legend(handles=[circle1], loc='upper center', ncol=1)  # , prop=font)
        ax4.legend(handles=[patch2], loc='upper center', ncol=1)  # , prop=font)
        ax5.legend(handles=[circle2], loc='upper center', ncol=1)  # , prop=font)

    # save
    fig.savefig(save_path, format=save_path[-3:], dpi=300)

    return


def visualize_uprn_or_epc_in_footprints(gdf_fp_count, case, save_path, section_size=150, include_legend=True):
    # define font
    plt.rcParams["font.family"] = "Calibri"
    plt.rcParams["font.size"] = "9"

    # initialize figure
    fig = plt.figure(constrained_layout=True, figsize=(7 * 0.3937, 7 * 0.3937))

    if include_legend:
        # define figure layout
        spec = gridspec.GridSpec(ncols=2,
                                 nrows=2,
                                 figure=fig,
                                 height_ratios=[0.95, 0.05],
                                 width_ratios=[0.6, 0.4])

        ax1 = fig.add_subplot(spec[0, :])
        ax2 = fig.add_subplot(spec[1, 0])
        ax3 = fig.add_subplot(spec[1, 1])


        ax2.axis('off')
    else:
        ax1 = fig.add_subplot()

    # remove axis ticks
    ax1.xaxis.set_ticks([])
    ax1.yaxis.set_ticks([])

    # define x and y limits
    gdf_fp_count = gpd.GeoDataFrame(gdf_fp_count)
    gdf_fp_count = gdf_fp_count.set_geometry("geom")
    bounds_1 = gdf_fp_count.geom.unary_union.bounds
    center_point_1 = Point(np.mean([bounds_1[0], bounds_1[2]]), np.mean([bounds_1[1], bounds_1[3]]))
    ax1.set_xlim([center_point_1.x - section_size / 2, center_point_1.x + section_size / 2])
    ax1.set_ylim([center_point_1.y - section_size / 2, center_point_1.y + section_size / 2])

    # distinguish between footprints with and without uprn
    gdf_fp_without = gdf_fp_count[gdf_fp_count[case+'_count'] == 0]
    gdf_fp_without = gdf_fp_without.set_geometry("geom")

    gdf_fp_with = gdf_fp_count[gdf_fp_count[case+'_count'] != 0]
    gdf_fp_with = gdf_fp_with.set_geometry("geom")

    gdf_fp_without.plot(ax=ax1, alpha=1, color=[115/255, 0, 42/255])
    gdf_fp_with.plot(ax=ax1, alpha=1, edgecolor="gray", linewidth=0.1, column=case+'_count', cmap='viridis_r')

    if include_legend:
        # # create the colorbar
        norm = colors.Normalize(vmin=gdf_fp_with[case+'_count'].min(), vmax=gdf_fp_with[case+'_count'].max())
        cbar = plt.cm.ScalarMappable(norm=norm, cmap='viridis_r')
        ax_cbar = fig.colorbar(cbar, cax=ax3, orientation='horizontal')
        ax_cbar.set_label(case + ' per footprint')

        # add patches as legend
        patch1 = mpatches.Patch(color=[115/255, 0, 42/255], edgecolor='none', alpha=0.7, label="no " + case)
        ax2.legend(handles=[patch1], loc='upper center', ncol=1)  # , prop=font)

    # save
    fig.savefig(save_path, format=save_path[-3:], dpi=300)

    return

