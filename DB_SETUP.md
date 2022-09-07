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
- run pdal pipeline to insert pointcloud data from .LAS file into database (can take a couple of minutes)
	- pdal pipeline --input pipeline_LAS_to_db.json
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