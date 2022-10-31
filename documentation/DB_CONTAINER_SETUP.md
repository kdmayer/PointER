## Containerized DB setup with extensions

### Vagrant Virtual Machine Setup:

Go to the [Singularity Docs](https://docs.sylabs.io/guides/3.0/user-guide/installation.html#install-on-windows-or-mac) and install Singularity.

From the respective Singularity folder, here vm-singularity, initialize the Virtual Machine with

    export VM=sylabs/singularity-3.0-ubuntu-bionic64 && \
    vagrant init $VM

Install the vagrant-disksize plugin with

    VAGRANT_DISABLE_STRICT_DEPENDENCY_ENFORCEMENT=1 vagrant plugin install vagrant-disksize

Add the following specifications to the Vagrantfile. They will be specified in between the following lines

        vagrant.configure('2') do |config|
            <<SPECIFICATION>>
        end

Specify the desired disk size in the Vagrantfile

        config.disksize.size = '150GB'

In order to use Jupyter Notebook from our VM, we also need to change the following line in our Vagrantfile

    # config.vm.network "forwarded_port", guest: 80, host: 8080

to

    config.vm.network "forwarded_port", guest: 8888, host: 8888


In order to share a folder from our host computer to the VM, we can specify the shared folder as

    config.vm.synced_folder "path/to/data_share", "/home/vagrant/data_share"

This way, we can easily exchange data between the VM and our host computer.

The first parameter specifies the host path (can be absolute or relative to the project folder "vm-singularity"). 
Make sure that the host folder exists.
The second parameter specifies the guest path. It should point to "/home/vagrant/" to be accessible in the singularity container.
The new guest folder will be created during spin up.

Afterwards, spin up the virtual machine with

    vagrant up && \
    vagrant ssh


### Increase partition size for vagrant
Even though we specified the disk size in the Vagrantfile to be 150GB, we require some further steps to liberate this space.
Steps are based on: https://nguyenhoa93.github.io/Increase-VM-Partition/

In the VM, we check the disk size with

    df -h

We need to increase the limited disk size of /dev/mapper/vagrant--vg-root (~19GB). First, we 

    sudo cfdisk /dev/sda

and use arrows to select sda1, then [Resize], specify space to 150GB, then [Write] and [Quit]. 
Next, we resize the physical volume

    sudo pvresize /dev/sda1

Then we expand the virtual volume

    sudo lvextend -r -l +100%FREE /dev/mapper/vagrant--vg-root


### Singularity Setup including pgpointcloud, conda, python environment and project folder
#### Pgpointcloud container with conda 
In the VM, create an empty container definition file

    touch cs224w.def

Install vim to manipulate file 

    sudo apt-get update && \
    sudo apt install vim

Copy the container definition file from this repo, i.e. cs224w.def, into your empty .def file in the VM

Build the .sif image from .def in the VM with

    sudo singularity build cs224w.sif cs224w.def

#### Pointcloud database setup
Singularity restricts writing directly to the container. Therefore, we need to create two directories on the VM. 
The folders are used by the pointcloud container to write required setup/configuration files. 

    mkdir -p $HOME/pgdata 
    mkdir -p $HOME/pgrun 

Then, we execute the database initialization. By binding both directories, we enable postgres to write on the VM.

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif initdb && \
    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif pg_ctl -D /var/lib/postgresql/data -l logfile start

Then, we can connect to the intial postgres database to check if the setup was successful

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif psql -d postgres

To conclude, using the postgres shell, we create a new database
    
    CREATE DATABASE cs224w_db;

and quit the postgres database:

    \q

to connect to our new cs224w_db base
    
    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif psql -d cs224w_db

Since it is a new database, we need to add the pointcloud and postgis extensions
    
    CREATE EXTENSION postgis;
	CREATE EXTENSION pointcloud;
	CREATE EXTENSION pointcloud_postgis;
    
Disconnect from database

    \q

For now, the database setup is complete. We will populate our pointcloud database with data later

#### Project 
We connect to the singularity container shell with 

    singularity shell cs224w.sif

Then, we set up our project with

    git clone https://github.com/kdmayer/CS224W_LIDAR.git

During the "git clone" step, you will need to provide your GitHub username and your access token.
    
To connect to the database with our python code, we define the database credentials in the config.py file. 
Based on the config_template.py, we adapt the connection parameters. 
Furthermore, we can specify a Google Maps API key, in case we want to download Google aerial images. 
Then we rename the file to config.py 

    cd CS224W_LIDAR && / 
    mv config_template.py config.py 

Then, we continue the set-up of the container with

    pip install conda-lock

#### Python environment
Make sure to add '/home/vagrant/.local/bin' to your $PATH, possibly to your .bashrc

    export PATH=$PATH:/home/vagrant/.local/bin

We install our conda environment and verify installation
    
    conda-lock install -n cs224w && \
    conda env list

In the shell, we run

    source /usr/local/etc/profile.d/conda.sh && \
    conda activate cs224w

Please note that specifying the path to conda.sh is needed when we want to activate conda in the singularity shell 

We manually install laspy with pip to make sure, laspy uses laszip, required for reading and writing LAZ files.
While our conda environment is active:

    pip install laspy[laszip]

### Add data to database: footprints, unique property reference numbers, and local authority boundary
#### Data sources
  - Building footprints:
    - We use verisk UKBuildings database (.gpkg): https://www.verisk.com/en-gb/3d-visual-intelligence/products/ukbuildings/
    - Alternatively, we can use OSM data
    - License for personal use only
  - Local Authority Distric Boundaries (.shp): https://geoportal.statistics.gov.uk/
    - Open Government Licencse
  - Unique Property Reference Numbers (UPRN) coordinates (.gpkg): https://www.ordnancesurvey.co.uk/business-government/products/open-uprn
    - Open Government Licencse
  - pointcloud data (.laz): UK National LiDAR Programme: https://www.data.gov.uk/dataset/f0db0249-f17b-4036-9e65-309148c97ce4/national-lidar-programme
    - Open Government Licencse

First, we need to make the data accessible to the VM. 
A simple way to copy-paste our data in the "share folder" we defined in the Vagrantfile.

Then, we move the data to project folder, so the singularity container can access them 
(not all of the VM's directories are accessible from within singularity):

    mv /home/vagrant/data_share/uprn.gpkg CS224W_LIDAR/assets/uprn/uprn.gpkg 
    mv /home/vagrant/data_share/UKBuildings_Edition_13_online.gpkg.gpkg CS224W_LIDAR/assets/footprints/UKBuildings_Edition_13_online.gpkg.gpkg
    mv /home/vagrant/data_share/local_authority_boundaries /local_authority_boundaries

Connect to singularity shell:

    singularity shell -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif 

To insert geopackage data into the database, we need GDALs ogr2ogr function. Therefor we activate the conda environment:

    source /usr/local/etc/profile.d/conda.sh && \
    conda activate cs224w

Using the conda GDAL installation, we insert the geopackage and shp data into our cs224w_db database. 
The data is some GBs and this process can take 15+ minutes.

Make sure, you are in home directory
    
    cd

then:

    ogr2ogr -nln uprn -nlt PROMOTE_TO_MULTI -lco GEOMETRY_NAME=geom -lco FID=gid -lco PRECISION=NO \
    -f PostgreSQL "PG:dbname='cs224w_db' host='localhost' port='5432' user='vagrant'" \
    CS224W_LIDAR/assets/uprn/uprn.gpkg
        
    ogr2ogr -nln footprints_verisk -nlt PROMOTE_TO_MULTI -lco GEOMETRY_NAME=geom -lco FID=gid -lco PRECISION=NO \
    -f PostgreSQL "PG:dbname='cs224w_db' host='localhost' port='5432' user='vagrant'" \
    CS224W_LIDAR/assets/footprints/UKBuildings_Edition_13_online.gpkg
    
    ogr2ogr -nln local_authority_boundaries -nlt PROMOTE_TO_MULTI -lco GEOMETRY_NAME=geom -lco FID=gid -lco PRECISION=NO \
    -f PostgreSQL "PG:dbname='cs224w_db' host='localhost' port='5432' user='vagrant'" \
    CS224W_LIDAR/assets/local_authority_boundaries/LAD_DEC_2021_GB_BFC.shp

See here for a description of input parameters: https://postgis.net/workshops/postgis-intro/loading_data.html

### Connect PyCharm Interpreter with Singularity Container:

To add the Singularity container as your Python Interpreter in PyCharm [follow these steps](https://www.jetbrains.com/help/pycharm/configuring-remote-interpreters-via-virtual-boxes.html)

In step 3, we specify 

    /home/vagrant/.conda/envs/cs224w/bin/python3.9

as the python location.

In PyCharm, we can connect to the container by clicking on the downward facing arrow in the terminal menu, and selecting the container

![Terminal Options](https://github.com/kdmayer/CS224W_LIDAR/blob/pg_pointcloud_benchmark/assets/images/Terminal.png)

Inside the container, spin up the container shell with 

    singularity shell cs224w.sif

And activate our conda environment with

    source /usr/local/etc/profile.d/conda.sh && \
    conda activate cs224w

You are all set.

### Run Jupyter Notebook from Vagrant VM:

In your vagrant container with the activated cs224w environment, run

    jupyter notebook --ip=0.0.0.0

You can then open the vagrant-based jupyter instance by visiting the following URL

    http://0.0.0.0:8888/tree

### Notes:

Note 1: If you have already created and used the vm-singularity folder for another VM, you will need to destroy the VM and delete the Vagrantfile.

From the vm-singularity folder, execute

        vagrant destroy && \
        rm Vagrantfile

Note 2: If you want to exit a running ssh session in your vagrant vm, simply type

    exit

in the command line interface.

Note 3: If you want to save a table or materialized view as gpkg or shp, you can use:

    ogr2ogr -f "GPKG" mynewfilename.gpkg PG:"host=localhost user=vagrant dbname=cs224w_db password=mypassword" "mytablename"