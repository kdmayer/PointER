# General remarks
The following description explains, how building point clouds for one area of interest (AOI) can be produced.
While generally any area of interest could be specified, in our case, the use of local authority districts as AOIs is preferred.
The local authority district boundaries are defined by the government and can be downloaded online.
In this description, we refer to the local authority district by name, e.g. York, as well as by local authority code (E06000014).

Before you start, make sure you have set up the database container as described in [DB_CONTAINER_SETUP.md](/documentation/DB_CONTAINER_SETUP.md).  
The description here assumes that you have set up a singularity container with a pgpointcloud database.
Furthermore, the database should contain building footprints, Unique Property Reference Numbers and 
Local Authority District Boundaries as described in the setup here: 
[adding data to database](https://github.com/kdmayer/CS224W_LIDAR/blob/main/documentation/DB_CONTAINER_SETUP.md#add-data-to-database-footprints-unique-property-reference-numbers-and-local-authority-boundary)

The process of running the code for one AOI contains 6 steps:

![img](/assets/images/overview.png)


# Prepare LiDAR data
## Download and unzip LiDAR tiles
URL: https://environment.data.gov.uk/DefraDataDownload/?Mode=survey

**1. Select area of interest (AOI) for download (two options)**

a) manually specify AOI as shown OR

![manual selection of AOI](/assets/images/manual_selection.png) 
  
b) create shapefile of district boundary

For this, from the vagrant machine, in the /home/vagrant folder,
first connect to the database in the singularity container: 

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif psql -d cs224w_db

If this fails, the database setting might need to be re-initialized first:

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif pg_ctl -D /var/lib/postgresql/data -l logfile start

Then run the first psql command again.

You will see that you are connected to the database in the terminal when the command line reads "cs224w_db=#"

Being connected, you can create a materialized view of an AOI boundary with this SQL query:

Note: This command requires that the "local_authority_boundaries" table data has been inserted as described

Note: The AOI Code "E06000014" is for the example of York and needs to be adapted for new AOIs respectively. 
If the materialized view already exists, this command will fail. 

    create materialized view "E06000014_boundary" as (
        select gid, st_simplify(labc.geom, 500) geom, lad21nm
        from local_authority_boundaries labc
        where labc.lad21cd='E06000014'
    );

Note: simplified geometry is required, because LiDAR download URL does not allow shapes with more than 1000 points. 
[see LiDAR URL](https://github.com/kdmayer/CS224W_LIDAR/blob/main/documentation/DB_CONTAINER_SETUP.md#add-data-to-database-footprints-unique-property-reference-numbers-and-local-authority-boundary)


You can test if the query was successful by querying the gid of the boundary

     select gid from "E06000014_boundary";

Next, export this materialized view to a shape file.
To do this, exit the database with 

    \q

Connect to the singularity container 

    singularity shell cs224w.sif

and activate the conda environment:

    source /usr/local/etc/profile.d/conda.sh && \
        conda activate cs224w

Then use the ogr2ogr program contained in the GDAL library to export the shape from the database
 
    ogr2ogr -f "ESRI Shapefile" CS224W_LIDAR/assets/local_authority_boundaries/E06000014_boundary_shp \
    PG:"dbname=cs224w_db host=localhost port=5432 user=vagrant" E06000014_boundary

The command creates a folder "E06000014_boundary_shp" in CS224W_LIDAR/assets/local_authority_boundaries and 
creates shapefiles there.

To zip this folder, first exit the singularity shell to go back to the vagrant machine to the home\vagrant\

    exit

Then run

    zip -r CS224W_LIDAR/assets/local_authority_boundaries/E06000014_boundary_shp.zip \
        CS224W_LIDAR/assets/local_authority_boundaries/E06000014_boundary_shp/

Note: If zip is not installed, first install zip:

    sudo apt install zip

Make zipped folder available to your computer by moving it to the data_share folder.

    mv CS224W_LIDAR/assets/local_authority_boundaries/E06000014_boundary_shp.zip \
    /home/vagrant/data_share/E06000014_boundary_shp.zip

You can then use this .zip file to download the LiDAR tiles in the boundary.
To do this, drag and drop the folder to the download page (https://environment.data.gov.uk/DefraDataDownload/?Mode=survey)

Note: Sometimes, through the simplification in the database query, an erroneous polygon is created. 
If you receive an error message after uploading the .zip, visualize the resulted boundary, 
and try out other simplification parameters, e.g. 600 instead of 500.

**2. Download .zip folders**

After marking the AOI, click on "Get available Tiles", then select "**National LiDAR Programme Point Cloud**", and download 
**all** LiDAR tiles for all available years, e.g. "2019" and "2020". Data should be from 2017 or newer. Resolution should be 1m.

Note: There is also a data type "LiDAR Point Cloud". Make sure NOT to select this one, because 
it contains the OLD LiDAR data with lower resolution. 

Note: For very large AOIs, it might be necessary to split the download into 2-3 sessions. The uploaded boundary can be 
used to visualize which tiles are included, but then the download area needs to be selected manually. 

**3. Unzip the downloaded .zip folders**
After the download, move to your download folder and unzip all LiDAR .zips. You will find the .laz files in one or 
multiple sub-folders.
After the download, move to the download folder and unzip all LiDAR .zips. The required .laz files will be in sub 
folders.

    unzip '*.zip'

## Download Energy Performance Certificates (EPC) data
URL: https://epc.opendatacommunities.org/

Download the EPC data. Most of the data is under the Open Government License, but the address information in the tables
is not under OGL, so an account is required for the download.
It is possible to download individual EPC data, but we recommend to download the entire dataset. 

The downloaded data is structured into folders according to local authority district (LAD) boundaries, e.g. York - E06000014.

![EPC downloaded](/assets/images/EPC_data_downloaded.png)

In the folders, there are "certificate.csv" files. Before using a file for a
region, rename it according to the local authority district code, e.g. "E06000014.csv". 
This way, the files won't be confused later on. 

## Upload LAZ files and EPC data to vagrant machine
Move the LiDAR .laz files & the EPC .csv file to the data_share folder, to make them accessible by the vagrant machine.
Make sure the EPC file is named according to LAD Code (e.g. "E06000014.csv" for York).

Optional: Delete existing data in "assets/uk_lidar_data" on the vagrant machine - to save storage space
Note: All pre-existing files from prior files exist in two versions: the downloaded .laz and the corresponding unpacked 
.las file. When running the program, all files that have already been unpacked are skipped and only "new" unpacked files 
are inserted into the database. So the program also skips previously existing and already unpacked files, even if they  are not deleted. 


In the vagrant VM, move the files to the "assets" folder ("assets/uk_lidar_data" and "assets/epc")
    
    mv /home/vagrant/data_share/E06000014.csv /home/vagrant/CS224W_LIDAR/assets/epc/E06000014.csv 
    mv /home/vagrant/data_share/folder_with_LAZ_files/* /home/vagrant/CS224W_LIDAR/assets/uk_lidar_data

## Adapt Script
Adapt AREA_OF_INTERST_CODE in building_pointcloud_main.py (line 26) to match Local Authority Boundary Code of the 
downloaded LiDAR data, e.g. "E06000014" for York. 

![configuration setting](/assets/images/configuration_setting.png)

Make sure to change only setting "AREA_OF_INTEREST_CODE".
The other settings affect the resulting point clouds and should be adapted consciously!

The setting "START_ITERATION" should be 0. 
It can be used for debugging or to restart the script after interruption.

## Adapt database
Delete or rename the existing "uk_lidar_data" table, because new data is appended.

The runtime of the program increases with larger point cloud data size, so it is desirable to reduce the table only 
relevant point cloud data. Data outside the region of interest slows down the process.  

To delete the existing table, connect to the database.
On the vagrant machine, in the home folder /home/vagrant, run 

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif psql -d cs224w_db

You should see "cs224w_db=#" in the terminal

    DROP TABLE uk_lidar_data;

The query is confirmed by "DROP TABLE" when successful
Then disconnect from the database:

    \q

## Run the code
Finally, in the vagrant VM, we connect to the singularity shell

    singularity shell cs224w.sif

and activate the conda environment:

    source /usr/local/etc/profile.d/conda.sh && \
        conda activate cs224w

change the directory to "src"

    cd CS224W_LIDAR/src

and run the program 
    
    python3 building_pointcloud_main.py

The program runs for several hours. The majority of time is spent on 3 blocks: 
1. Converting .laz to .las and inserting the data in the database
2. Getting the point clouds in footprints by SQL query (this process chunked)
3. Adding floor points to the point clouds (this process is chunked)
The results are saved in every loop, so the program could be restarted after interruption  


## Result
After the program ran successfully, the resulting folder should look like this:

![result folder](/assets/images/result_folder.png)

**Files:**
- epc_E0600014.json: EPC efficiency label of buildings in AOI
- final_E06000014.geojson: final result mapping labels to point cloud filename and footprint polygon
- footprints_E06000014.geojson: footprint polygon data
- production_metrics_E06000014.json: a summary of number of footprints in AOI and number of building point clouds produced 
- uprn_E06000014.geojson: Unique Property Reference Numbers point data 

Please note that the footprint polygon data is removed from the published dataset due to license agreement

**Folders:**

- The **building point clouds** are stored in .npy format in the **"npy_raw"** folder.
- All other folders contain data of the .json file with the same name for one of the chunks. 
  - E.g. "epc_E06000026_0.json" contains the EPC labels of the first iteration of the program. 
  - The chunks' data is stitched together at the end of the iterations.
  - The "filename_mapping" folder contains the data snippets used for the "final_EXXXXXXXX.geojson" result file.