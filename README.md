## Setup Instructions

Clone repo to your local machine. Navigate into root directory.

To get started, initialize and activate the environment with

    conda env create --file=environment.yml
    conda activate cs224w

## Get started with postgres database and pgpointcloud extension
### Create database and install extensions
- if not yet installed: install postgres (https://ubuntu.com/server/docs/databases-postgresql)
- connect to postgres server (psql -U postgres)
- create a new database https://www.postgresql.org/docs/current/sql-createdatabase.html
- install postgis and pgpointcloud extension 
	- install extensions on machine: 
	apt install postgis; apt install postgresql-10-pgpointcloud; apt install postgresql-10-pgpointcloud_postgis
	- install extensions in database:
	CREATE EXTENSION postgis;
	CREATE EXTENSION pointcloud;
	CREATE EXTENSION pointcloud_postgis;
### Populate database with lidar pointcloud data and building footprint data
- install pdal if not yet installed
- install laszip to be able to run pdal pipeline with .LAZ file.
	- in case of issues: https://github.com/laspy/laspy/issues/79
- unzip .LAZ file to .las file
	- laszip [laszipfilename.laz]
- run pdal pipeline to insert pointcloud data from .LAZ file into database (can take a couple of minutes)
	- pdal pipeline --input pipeline_LAZ_to_db.json
- insert building footprints into database using ogr2ogr
	- ogr2ogr -f "PostgreSQL" PG:"host=localhost dbname=postgres user=krapf password=krapf port=5432" coventry_building_footprints.geojson -nln footprints

### Create spatial indexes to speed up SQL queries significantly
- index for building footprints (might already contain spatial index because of ogr2ogr import)
	- CREATE INDEX geoid ON footprints USING GIST (wkb_geometry); 
	- VACUUM ANALYZE footprints (wkb_geometry);
- index for point cloud data 
	- CREATE INDEX patches_idx on pointcloud_test using GIST (Geometry(pa));  
	- VACUUM ANALYZE pointcloud_test (pa);


Now you are ready to use the pgpointcloud functions to crop lidar points according to building footprints
    
 ## TODOs.md
 
 TODOs.md helps us to keep track of our progress and TODO items. 
 
 Please specify the date and the author name when adding new TODOs. 
    
## Important Note: 

 - **Please do not push your changes directly to the main branch.**
 - Instead, let's develop features locally with the help of feature branches and push them to the remote with a Pull Request (PR). 
 - Suggested format for local branches: feature_name_your_name, e.g. feature_embedding_kevin
 - To save us from tedious debugging sessions, we will not merge PRs which do not execute successfully on local machines.

## Exemplary PDAL Output from Point_Cloud_Demo.ipynb
 
 ![PDAL Output](https://github.com/kdmayer/CS224W_LIDAR/blob/main/assets/images/example.png)
 


