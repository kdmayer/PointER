# Prepare LiDAR data
## Download and unzip LiDAR tiles
URL: https://environment.data.gov.uk/DefraDataDownload/?Mode=survey
1. Select area of interest (AOI) for download (two options)

a) manually specify AOI as shown in assets/images/manual_selection.png OR 

b) create shapefile of district boundary

Create a materialized view of AOI boundary with this SQL query. 
Note: simplified geometry is required, because URL does not allow shapes with more than 1000 points.

    create materialized view "E06000014" as (
        select gid, st_simplify(labc.geom, 500) geom, lad21nm
        from local_authority_boundaries labc
        where labc.lad21cd='E06000014'
    )

Then, export this materialized view to a shape file with this command.

    ogr2ogr -f "ESRI Shapefile" assets/local_authority_boundaries/E06000014_boundary_shp \
    PG:"dbname=cs224w_db host=localhost port=5432 user=vagrant" E06000014

The command creates a folder "E06000014_boundary_shp" in assets/local_authority_boundaries and creates shapefiles there.
Zip this folder

    zip assets/local_authority_boundaries/E06000014_boundary_shp.zip assets/local_authority_boundaries/E06000014_boundary_shp/

Then drag and drop the folder to the download page.
Note: Sometimes, through the simplification in the database query, an erroneous polygon is created. If receive an error
message after uploading the .zip, visualize the resulted boundary, and try out other simplification parameters, e.g. 
600 instead of 500.

2. Download .zip folders 
After marking the AOI, click on "Get available Tiles", then select "National LiDAR Programme Point Cloud", and download 
all LiDAR tiles for all available years, e.g. "2019" and "2020". Data should be from 2017 or newer.
Note: Resolution should be 1m. There is also a data type "LiDAR Point Cloud". Make sure NOT to select this one, because 
it contains the OLD LiDAR data with lower resolution. 

3. Unzip the downloaded .zip folders 
After the download, move to the download folder and unzip all LiDAR .zips. The required .laz files will be in sub 
folders. Move all .laz files to your desired storage location.


    unzip '*.zip'

## Download Energy Performance Certificates (EPC) data
URL: https://epc.opendatacommunities.org/
Download the EPC data. Most of the data is under the Open Government License, but the address information in the tables
is not under OGL, so an account is required for the download.
It is possible to download individual EPC data, but we recommend to download the entire dataset. The downloaded data is
structured into folders according to local authority district (LAD) boundaries, e.g. York - E06000014. 
(see assets/images/EPC_data_downloaded). In the folders, there is a "certificate.csv" file. Before using the file for a
region, rename it according to the code, e.g. "E06000014.csv"

## Upload LAZ files and epc data to vagrant machine
Move the LiDAR .laz files & the EPC .csv file to the data_share folder, to make them accessible by the vagrant machine.
Make sure the EPC file is named according to LAD Code (e.g. "E06000014.csv" for York).

Optional: Delete existing data in "assets/uk_lidar_data" on the vagrant machine - to save storage space
    Note: All existing files should exist as .laz as well as .las, and the program only insert .laz files to database 
    if corresponding .las does not exist, so the program should work anyway, if this step is skipped.

Move the files to the "assets" folder ("assets/uk_lidar_data" and "assets/epc")
    
    mv /home/vagrant/data_share/E06000014.csv /home/vagrant/CS224W_LIDAR/assets/epc/E06000014.csv 
    mv /home/vagrant/data_share/folder_with_LAZ_files /home/vagrant/CS224W_LIDAR/assets/uk_lidar_data

## Adapt Scipt
Adapt AREA_OF_INTERST_CODE in building_pointcloud_main.py (line 40) to match Local Authority Boundary Code of the 
downloaded LiDAR data, e.g. "E06000014" for York. (see assets/images/configuration_setting.png)
Make sure to change only setting "AREA_OF_INTEREST_CODE".
The other settings affect the resulting point clouds and should be adapted consciously!
The setting "START_ITERATION" should be 0. 
It can be used for debugging or to restart the script after interruption.

## Adapt database
Delete or rename the existing "uk_lidar_data" table, because new data is appended.

    DROP TABLE uk_lidar_data;

The runtime of the program increases with larger point cloud data size, so it is desirable to reduce the table only 
relevant point cloud data. Data outside of the region of interest slows down the process.  
This can be done in database administration software (DBeaver/pgadmin4) or by connection through console:

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif psql -d cs224w_db


## Run the code
Finally, connect to the singularity shell
    
    singularity shell cs224w.sif

and run the program 
    
    python3 building_pointcloud_main.py

The majority of time is spent on 3 blocks: 
1. Converting .laz to .las and inserting the data in the database
2. Getting the point clouds in footprints by SQL query (this process chunked)
3. Adding floor points to the point clouds (this process is chunked)
The results are saved in every loop, so the program could be restarted after interruption  