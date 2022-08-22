from typing import List

import plotly.graph_objects as go
import numpy as np


def visualize_3d_array(point_cloud_array: np.ndarray = None, file_name_list: List = None, example_ID=None):
    x = point_cloud_array[example_ID, :, 0].flatten()
    y = point_cloud_array[example_ID, :, 1].flatten()
    z = point_cloud_array[example_ID, :, 2].flatten()

    scatter = go.Scatter3d(x=x, y=y, z=z, mode='markers',
                           marker=dict(size=3, color=z, colorscale='Viridis'))
    layout = go.Layout(title=f'Visualization of {file_name_list[example_ID]}')
    fig = go.Figure(data=[scatter], layout=layout)
    fig.show()
    return