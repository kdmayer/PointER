# Prepare LiDAR data
## Download and unzip LiDAR tiles
URL:
1. Select area of interest (AOI)

   a) manually specify AOI

   b) create shapefile of district boundary

2. Download .zip folders 

3. Unzip the downloaded .zip folders 

## Upload LAZ files and epc data to vagrant machine
Move the LiDAR .laz files & the EPC .csv file to the data_share folder, to make them accessible by the vagrant machine.
Make sure the EPC file is named according to LAD Code (e.g. "E06000014.csv" for York).

Optional: Delete existing data in "assets/uk_lidar_data" on the vagrant machine - to save storage space
    Note: All existing files should exist as .laz as well as .las, and the program only insert .laz files to database 
    if corresponding .las does not exist, so the program should work anyway, if this step is skipped.

Move the files to the "assets" folder ("assets/uk_lidar_data" and "assets/epc")
    
    mv ...

## Adapt Scipt
Adapt AREA_OF_INTERST_CODE in building_pointcloud_main.py (line 40) to match Local Authority Boundary Code of the downloaded LiDAR data,
e.g. "E06000014" for York.

## Adapt database
Delete existing uk_lidar_data table, because new data is appended.
The runtime of the program increases with larger point cloud data size, so it is desirable to reduce the table only 
relevant point cloud data. Data outside of the region of interest slows down the process.  
This can be done in database administration software (DBeaver/pgadmin4) or by connection through console:

    DROP TABLE uk_lidar_data;

## Run the code
python3 building_pointcloud_main.py