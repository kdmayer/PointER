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

## Dataset
The [dataset](https://mediatum.ub.tum.de/1713501) contains one million building point clouds for 16 Local Authority Districts in England.
These Local Authority Districts are representative for the English building stock and selected across the country (see image).

![img](/assets/images/LAD_selected.png)

This is an example of a resulting point cloud:
![img](/assets/images/example.png)

## Data Sources
- Point cloud data (.laz): [UK National LiDAR Programme](https://www.data.gov.uk/dataset/f0db0249-f17b-4036-9e65-309148c97ce4/national-lidar-programme)
  - Open Government Licencse
- We use [Verisk UKBuildings database](https://www.verisk.com/en-gb/3d-visual-intelligence/products/ukbuildings/) (.gpkg format) as building footprints
  - License for personal use only
  - Alternatively, we can use OSM data
- [Local Authority Distric Boundaries](https://geoportal.statistics.gov.uk/) (.shp format) 
  - Open Government Licencse
- [Unique Property Reference Numbers](https://www.ordnancesurvey.co.uk/business-government/products/open-uprn) (UPRN) including coordinates (.gpkg format) 
  - Open Government Licencse


## Versioning
V0.1 Initial version

## Citation

    @article{Krapf2023,
      doi = {10.1038/s41597-023-02544-x},
      url = {https://doi.org/10.1038/s41597-023-02544-x},
      year = {2023},
      publisher = {Springer Science and Business Media {LLC}},
      volume = {10},
      author = {Sebastian Krapf and Kevin Mayer and Martin Fischer},
      title = {Points for energy renovation ({PointER}): A point cloud dataset of a million buildings linked to energy features},
      journal = {Scientific Data}
    }

## License
This project is licensed under the [MIT License](LICENSE).
