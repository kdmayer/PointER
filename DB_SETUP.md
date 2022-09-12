## Get started with postgres database and pgpointcloud extension
### Create database and install extensions
- if not yet installed: install postgres (https://ubuntu.com/server/docs/databases-postgresql)
    sudo apt install postgresql
- install postgis and pgpointcloud extensions on machine: 
	apt install postgis; apt install postgresql-10-pgpointcloud; apt install postgresql-10-pgpointcloud_postgis
- connect to postgres server 
    sudo psql -U postgres
- create a new database https://www.postgresql.org/docs/current/sql-createdatabase.html
    CREATE DATABASE my_pointcloud_db;
- create a new user with password
    CREATE USER user WITH PASSWORD 'password';
- install postgis and pgpointcloud extension in database (while beeing connected to postgres server)
	CREATE EXTENSION postgis;
	CREATE EXTENSION pointcloud;
	CREATE EXTENSION pointcloud_postgis;
