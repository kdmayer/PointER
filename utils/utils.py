from shapely.geometry import box

import numpy as np

import laspy
import shapely


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


def subsample_las(original_las_data_filepath: str = None, random_sample_size: int = 100000):
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


def normalize_geom(geom: shapely.geometry = None, scaling_factor: int = 1000, random_sample_size: int = None):
    if len(geom.geoms) >= random_sample_size:
        # scale x coordinates
        new_x = np.array([g.x for g in geom.geoms])
        new_x = (new_x - new_x.min()) / scaling_factor
        # scale y coordinates
        new_y = np.array([g.y for g in geom.geoms])
        new_y = (new_y - new_y.min()) / scaling_factor
        # scale z coordinates
        new_z = np.array([g.z for g in geom.geoms])
        new_z = (new_z - new_z.min()) / scaling_factor
        # create numpy array from coordinates
        lidar_numpy = np.array((new_x, new_y, new_z)).transpose()
        # subsample numpy array
        lidar_numpy = _sample_random_points(lidar_numpy, random_sample_size)
    else:
        lidar_numpy = []
        print('not enough points')
    return lidar_numpy


def normalize_point_cloud_gdf(gdf_pc, scaling_factor: int = 1000, random_sample_size: int = None):
    # lidar_numpy_list = []
    # normalize to values between 0 and 1
    # for i, geom in enumerate(gdf_pc.geom):
    #     print(i)
    #     if len(geom.geoms) >= random_sample_size:
    #         lidar_numpy = normalize_geom(geom, scaling_factor, random_sample_size)
    #         lidar_numpy_list.append(lidar_numpy)
    #     else:
    #         print('sample ' + str(i) + ' skipped because number of points is lower than required sample size')

    lidar_numpy_list = list(gdf_pc.geom.apply(normalize_geom, args=[scaling_factor, random_sample_size]))

    return lidar_numpy_list



def create_tile_bounding_box(original_las_data_filepath: str = None):
    las_data = laspy.read(original_las_data_filepath)
    min_x, min_y, min_z, max_x, max_y, max_z = [*las_data.header.min, *las_data.header.max]
    return box(minx=min_x, miny=min_y, maxx=max_x, maxy=max_y)




