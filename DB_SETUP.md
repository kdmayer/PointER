## Get started with postgres database and pgpointcloud extension
### Install postgresql and extensions postgis and pgpointcloud on machine
- first update apt
    
    
    sudo apt update
    
- if not yet installed: install postgres (https://ubuntu.com/server/docs/databases-postgresql)


    sudo apt install postgresql-10
    
- install postgis and pgpointcloud extensions on machine: 


    sudo apt install postgis 
    sudo apt install postgresql-10-pointcloud
    
- if "Unable to locate package postgresql-10-pointcloud", check if package is available (possible typo) 


    sudo apt-cache search postgresql-10
    
- follow this instruction to add postgres repository to apt
	 (https://wiki.postgresql.org/wiki/Apt)
	 
### Create database and install extensions in database
- connect to postgres server 
    
    
    sudo psql -U postgres
    
- create a new database (https://www.postgresql.org/docs/current/sql-createdatabase.html)


    CREATE DATABASE my_pointcloud_db;
    
- optional: create a new user with password


    CREATE USER my_new_user WITH PASSWORD 'my_password';
    
- exit psql with \q
- connect to database with credentials    
    
    
    psql -h 'localhost' -p '5432' -U 'my_new_user' -d 'my_pointcloud_db'
    
- install postgis and pgpointcloud extension in database (while beeing connected to postgres server)
	
	
	CREATE EXTENSION postgis;
	CREATE EXTENSION pointcloud;
	CREATE EXTENSION pointcloud_postgis;


