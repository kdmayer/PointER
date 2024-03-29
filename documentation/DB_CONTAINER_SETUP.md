## Containerized DB setup with extensions

### Vagrant Virtual Machine Setup:

Go to the [Singularity Docs](https://docs.sylabs.io/guides/3.0/user-guide/installation.html#install-on-windows-or-mac) and install Singularity.

Create a new folder for the VM, name it "vm-singularity" and move to the folder.

    mkdir vm-singularity
    cd vm-singularity

From the respective Singularity folder (vm-singularity), initialize the Virtual Machine with

    export VM=sylabs/singularity-3.0-ubuntu-bionic64 && \
    vagrant init $VM

Install the vagrant-disksize plugin with

    VAGRANT_DISABLE_STRICT_DEPENDENCY_ENFORCEMENT=1 vagrant plugin install vagrant-disksize

Add specifications to the Vagrantfile. They will be specified in between the following lines

        vagrant.configure('2') do |config|
            <<SPECIFICATION>>
        end

Specify the desired disk size in the Vagrantfile

        config.disksize.size = '150GB'

To provide enough working memory for the large LAZ point cloud files, we need to change the memory.
We ran the process with 48 GB of RAM. 
The provided example works with 4 GB of RAM, but usually, the point clouds are larger and will require more memory.
      
    config.vm.provider "virtualbox" do |vb|
      #   # Customize the amount of memory on the VM:
        vb.memory = "4096"
    end

In order to use Jupyter Notebook from our VM, we also need to change the following line in our Vagrantfile

    # config.vm.network "forwarded_port", guest: 80, host: 8080

to

    config.vm.network "forwarded_port", guest: 8888, host: 8888


In order to share a folder from our host computer to the VM, we can specify the shared folder as

    config.vm.synced_folder "path/to/data_share", "/home/vagrant/data_share"

This way, we can easily exchange data between the VM and our host computer.

The first parameter specifies the host path (can be absolute or relative to the project folder "vm-singularity"). 
**Make sure that the host folder exists** or create it, otherwise the spin up of the virtual machine will fail.

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

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif initdb -E UTF8 --locale=C && \
    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif pg_ctl -D /var/lib/postgresql/data -l logfile start

Then, we can connect to the initial postgres database to check if the setup was successful

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif psql -d postgres

You should see "postgres=#" on the left of your command line.

To conclude, using the postgres shell, we create a new database
    
    CREATE DATABASE cs224w_db;

and quit the postgres database

    \q

to connect to our new cs224w_db base
    
    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif psql -d cs224w_db

You should see "cs224w_db=#" on the left of your command line.

Since it is a new database, we need to add the poin tcloud and postgis extensions
    
    CREATE EXTENSION postgis;
	CREATE EXTENSION pointcloud;
	CREATE EXTENSION pointcloud_postgis;
    
Disconnect from database

    \q

For now, the database setup is complete. We will populate our point cloud database with data later.

#### Project 
We connect to the singularity container shell with 

    singularity shell cs224w.sif

Then, we set up our project with

    git clone https://github.com/kdmayer/CS224W_LIDAR.git

During the "git clone" step, you will need to provide your GitHub username and your access token.
    
To connect to the database with our python code, we define the database credentials in the config.py file. 
Based on the config_template.py, we adapt the connection parameters. 
Furthermore, we can specify a Google Maps API key, in case we want to download Google aerial images. 

To do this, we disconnect from the singularity container with 

    exit

and then move to the CS224W_LIDAR folder and adapt the file by:

    cd CS224W_LIDAR
    vim config_template.py

Then we reconnect to the singularity container with

    singularity shell cs224w.sif

and we rename the config_template.py file to config.py 

    cd CS224W_LIDAR && \ 
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

To make the data accessible to our VM, we copy and paste the data into the "data_share" 
folder specified in the Vagrantfile.

To set up the database, we move the data to the project folder. By moving the data to the project folder, we ensure 
that the singularity container can access the data. 
Note that not all of the VM's directories are accessible from within singularity.

Note that the following commands work for example files of York. 
The filenames need to be adapted when working with the full datasets.

    mv /home/vagrant/data_share/uprn_york.gpkg /home/vagrant/CS224W_LIDAR/assets/uprn/uprn_york.gpkg 
    mv /home/vagrant/data_share/footprints_verisk_york.gpkg /home/vagrant/CS224W_LIDAR/assets/footprints/footprints_verisk_york.gpkg
    mv /home/vagrant/data_share/local_authority_boundaries_york.gpkg /home/vagrant/CS224W_LIDAR/assets/local_authority_boundaries/local_authority_boundaries_york.gpkg
    
We also move 2 files which will be required when running the program to the assets folder (preparation for later)

    mv /home/vagrant/data_share/E06000014.csv /home/vagrant/CS224W_LIDAR/assets/epc/E06000014.csv 
    mv /home/vagrant/data_share/SE6053_P_11311_20171109_20171109.laz /home/vagrant/CS224W_LIDAR/assets/uk_lidar_data/SE6053_P_11311_20171109_20171109.laz

As an example, the following commands demonstrate the workflow for York. To run the code for other AoIs, we need to 
adapt the filenames accordingly.

Connect to singularity shell:

    singularity shell -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif 

To insert geopackage data into the database, we need GDALs ogr2ogr function. Therefore, we activate the conda environment:

    source /usr/local/etc/profile.d/conda.sh && \
    conda activate cs224w

Using the conda GDAL installation, we insert the .gpkg and .shp data into our cs224w_db database. 
This process can take 15+ minutes, but with the example data for York, this should only take seconds.

Make sure, you are in home directory, then:

    ogr2ogr -nln uprn -nlt PROMOTE_TO_MULTI -lco GEOMETRY_NAME=geom -lco FID=gid -lco PRECISION=NO \
    -f PostgreSQL "PG:dbname='cs224w_db' host='localhost' port='5432' user='vagrant'" \
    /home/vagrant/CS224W_LIDAR/assets/uprn/uprn_york.gpkg
     
    ogr2ogr -nln footprints_verisk -nlt PROMOTE_TO_MULTI -lco GEOMETRY_NAME=geom -lco FID=gid -lco PRECISION=NO \
    -f PostgreSQL "PG:dbname='cs224w_db' host='localhost' port='5432' user='vagrant'" \
    /home/vagrant/CS224W_LIDAR/assets/footprints/footprints_verisk_york.gpkg

    ogr2ogr -nln local_authority_boundaries -nlt PROMOTE_TO_MULTI -lco GEOMETRY_NAME=geom -lco FID=gid -lco PRECISION=NO \
    -f PostgreSQL "PG:dbname='cs224w_db' host='localhost' port='5432' user='vagrant'" \
    /home/vagrant/CS224W_LIDAR/assets/local_authority_boundaries/local_authority_boundaries_york.gpkg

Note: This example works with the provided file snippets for York. Make sure to adapt the filenames when running
the setup for other AoIs. Instead of the .gpkg format, .shp files could also be imported with the same command.

See here for a description of input parameters: https://postgis.net/workshops/postgis-intro/loading_data.html

After loading the data into the database, we can try out the program in a jupyter notebook:
See the description of how to run jupyter notebook from vagrant vm in "Notes" below.
Make sure to be in the CS224W_LIDAR folder when running the notebook.

    experimentation/building_pointcloud_generation.ipynb 

to generate building point clouds for York.

To generate building point clouds for the entire AOI of York or other AOIs, please see the detailed description:

    documentation/RUN_POINTCLOUD_GENERATION.md


### Notes:

#### Connect PyCharm Interpreter with Singularity Container:

To add the Singularity container as your Python Interpreter in PyCharm [follow these steps](https://www.jetbrains.com/help/pycharm/configuring-remote-interpreters-via-virtual-boxes.html)

In step 3, we specify 

    /home/vagrant/.conda/envs/cs224w/bin/python3.9

as the python location.

In PyCharm, we can connect to the container by clicking on the downward facing arrow in the terminal menu, and selecting the container

![Terminal Options](https://github.com/kdmayer/CS224W_LIDAR/blob/main/assets/images/Terminal.png)

Inside the container, spin up the container shell with 

    singularity shell cs224w.sif

And activate our conda environment with

    source /usr/local/etc/profile.d/conda.sh && \
    conda activate cs224w

You are all set.

#### Run Jupyter Notebook from Vagrant VM:

Option 1: In your vagrant container with the activated cs224w environment, run

    jupyter notebook --ip=0.0.0.0

You can then open the vagrant-based jupyter instance by visiting the following URL

    http://0.0.0.0:8888/tree

Option 2: If the option above doesn't work, try the following:

In the vagrant container, activate your conda environment and run

    jupyter notebook --no-browser --port=YOUR_PORT --ip=0.0.0.0

Now, on your local machine, open a web browser and type this url: 

    http://localhost:YOUR_PORT

#### Destroy existing VM

If you have already created and used the vm-singularity folder for another VM, you will need to destroy the VM and delete the Vagrantfile.

From the vm-singularity folder, execute

    vagrant destroy && \
    rm Vagrantfile

#### Exit running ssh session

If you want to exit a running ssh session in your vagrant vm, simply type

    exit

in the command line interface.

#### Save table as .gpkg or .shp

If you want to save a table or materialized view as .gpkg or .shp, you can use:

    ogr2ogr -f "GPKG" mynewfilename.gpkg PG:"host=localhost user=vagrant dbname=cs224w_db password=mypassword" "mytablename"