from shapely.geometry import box

import numpy as np

import laspy




def _convert_numpy_to_las(x: np.ndarray = None, header=None):
    outfile = laspy.LasData(header)
    outfile.x = x[:, 0]
    outfile.y = x[:, 1]
    outfile.z = x[:, 2]
    outfile.intensity = x[:, 3]
    outfile.raw_classification = x[:, 4]
    outfile.scan_angle_rank = x[:, 5]

    return outfile


def _sample_random_points(x: np.ndarray = None, random_sample_size: int = None):
    rng = np.random.default_rng()
    lidar_subset = rng.choice(a=x, size=random_sample_size, replace=False, axis=0)

    return lidar_subset


def _convert_las_to_numpy(las_data=None):
    lidar_numpy = np.array((las_data.x,
                            las_data.y,
                            las_data.z,
                            las_data.intensity,
                            las_data.raw_classification,
                            las_data.scan_angle_rank)).transpose()

    return lidar_numpy


def subsample_las(original_las_data_filepath: str = None, random_sample_size: int = 1000000):
    org_las_data = laspy.read(original_las_data_filepath)
    # Set meta data for new LAS file based on settings from original LAS file
    hdr = org_las_data.header
    hdr.point_count = 0

    lidar_ndarray = _convert_las_to_numpy(las_data=org_las_data)
    print(f"SHAPE of LIDAR: {lidar_ndarray.shape}")

    lidar_subset = _sample_random_points(x=lidar_ndarray, random_sample_size=random_sample_size)
    print(f"SHAPE of LIDAR_SUBSET: {lidar_subset.shape}")

    outfile = _convert_numpy_to_las(lidar_subset, hdr)
    output_filepath = original_las_data_filepath[:-4] + "_SUBSET.las"

    print(f"Saving subsampled LAS file to: {output_filepath}")
    outfile.write(output_filepath)

    return outfile


def create_tile_bounding_box(original_las_data_filepath: str = None):
    las_data = laspy.read(original_las_data_filepath)
    min_x, min_y, min_z, max_x, max_y, max_z = [*las_data.header.min, *las_data.header.max]
    return box(minx=min_x, miny=min_y, maxx=max_x, maxy=max_y)