import os

import numpy as np
import plotly.graph_objects as go

from typing import List

from utils.utils import point_cloud_xyz


def cm_to_inch(length_cm):
    length_inch = length_cm * 0.3937
    return length_inch


# Define image size
def get_image_size(version):
    max_width = 14.7
    if version == 'small':
        img_size_x = cm_to_inch(max_width * 2 / 3)
        img_size_y = img_size_x
    elif version == 'wide':
        img_size_x = cm_to_inch(max_width)
        img_size_y = img_size_x / 6
    elif version == 'large':
        img_size_x = cm_to_inch(max_width)
        img_size_y = img_size_x / 4
    elif version == 'one_third_large':
        img_size_x = cm_to_inch(max_width)
        img_size_y = img_size_x / 3
    elif version == "squared_large":
        img_size_x = cm_to_inch(max_width)
        img_size_y = img_size_x

    return img_size_x, img_size_y


def visualize_3d_array(point_cloud_array: np.ndarray = None, file_name_list: List = None, example_ID=None):
    x, y, z = point_cloud_xyz(point_cloud_array)
    scatter = go.Scatter3d(x=x, y=y, z=z, mode='markers',
                           marker=dict(size=3, color=z, colorscale='Viridis'))
    layout = go.Layout(title=f'Visualization of {file_name_list[example_ID]}')
    fig = go.Figure(data=[scatter], layout=layout)
    fig.show()
    return


def visualize_single_3d_point_cloud(point_cloud_array: np.ndarray = None, title: str = 'title', save_path: str = None,
                                    show: bool = False, format: str = 'html'):
    x, y, z = point_cloud_xyz(point_cloud_array)
    scatter = go.Scatter3d(x=x, y=y, z=z, mode='markers',
                           marker=dict(size=3, color=z, colorscale='Viridis'))
    layout = go.Layout(title=f'Visualization of {title}')
    fig = go.Figure(data=[scatter], layout=layout)

    if show:
        fig.show()
    if format == 'html':
        fig.write_html(save_path)
    elif format == 'png':
        fig.write_image(save_path)
    return


def visualize_example_pointclouds(lidar_numpy_list: list, DIR_VISUALIZATION: str,
                                  NUMBER_EXAMPLE_VISUALIZATIONS: int = 1):
    for i, lidar_pc in enumerate(lidar_numpy_list):
        if i <= NUMBER_EXAMPLE_VISUALIZATIONS:
            visualize_single_3d_point_cloud(
                lidar_pc,
                title=str(i),
                save_dir=DIR_VISUALIZATION,
                show=False
            )


def batch_visualization(DIR_POINT_CLOUDS, DIR_SAVE, format: str = 'html', status_update: bool = False,
                        number_examples=None):
    pc_file_names = os.listdir(DIR_POINT_CLOUDS)
    if number_examples == None:
        number_examples = len(pc_file_names)
    count = 0
    for pc_file_name in pc_file_names:
        if status_update and count % 100 == 0:
            print('Running batch visualization in ' + str(format) + ' of images ' +
                  str(count) + ' out of ' + str(number_examples))
        if count <= number_examples:
            count += 1
            pc_file_path = os.path.join(DIR_POINT_CLOUDS, pc_file_name)
            point_cloud_array = np.load(pc_file_path)
            # normalize pc array for visualization
            for i in np.arange(0, 3):
                point_cloud_array[:, i] = (point_cloud_array[:, i] - point_cloud_array[:, i].min())

            save_path = os.path.join(DIR_SAVE, str(pc_file_name[:-4] + '.' + format))
            visualize_single_3d_point_cloud(point_cloud_array, title=pc_file_name, save_path=save_path,
                                            show=False, format=format)
    return

