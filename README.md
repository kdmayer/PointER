# Points for Energy Renovation (PointER): 
## A LiDAR-Derived Point Cloud Dataset of One Million English Buildings Linked to Energy Characteristics

## Getting Started
- Please see our [setup documentation](documentation/DB_CONTAINER_SETUP.md) for a step by step description.
- Please check our related paper for information about the method and the resulting dataset.
The pre-print version is available [here](https://arxiv.org/abs/2306.16020). 
- A dataset comprising one million building point clouds with half of the buildings linked to energy features is available [here](https://mediatum.ub.tum.de/1713501).

## Prerequisites
- Required packages are documented in the [environment.yml](environment.yml) file. 
- The [environment_for_analysis.yml](environment_for_analysis.yml) includes some more packages required for visualization and analysis.

## Running the Code
- To run an example point cloud generation, please use the [jupyter notebook](experimentation/building_pointcloud_generation.ipynb).
- To run the point cloud generation for an entire area of interest, please see the [point cloud generation documentation](documentation/RUN_POINTCLOUD_GENERATION.md).
- The main program can be found [here](src/building_pointcloud_main.py). Please note, that the point cloud generation process involves some upfront data preparation.

The process involves 6 steps:

![img](/assets/images/overview.png)

Due to the size of the point cloud files, it is recommended to set up the container on a machine with a large working memory. 
We ran the code without problems on a machine with 48 GB, but a machine with 16 GB or more should work.

## Versioning
V0.1 Initial version

## Authors
Author: Sebastian Krapf, Kevin Mayer

## License
This project is licensed under the [MIT License](LICENSE).
