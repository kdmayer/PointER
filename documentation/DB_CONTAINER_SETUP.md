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

Furthermore, we add the following line to enable working with postgres  

    config.vm.network "forwarded_port", guest: 5454, host: 5454, host_ip: "127.0.0.1"


In order to share a folder from our host computer to the VM, we can specify the shared folder as

    config.vm.synced_folder "data_share", "/home/vagrant/data_share"

This way, we can easily exchange data between the VM and our host computer.

The first parameter specifies the host path (can be absolute or relative to the project folder "vm-singularity"). 
Make sure that the host folder exists.
The second parameter specifies the guest path. It should point to "/home/vagrant/" to be accessible in the singularity container.
The new guest folder will be created during spin up.

Afterwards, spin up the virtual machine with

    vagrant up && \
    vagrant ssh

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
The folder are used by the pointcloud container to write required setup/configuration files. 

    mkdir -p $HOME/pgdata 
    mkdir -p $HOME/pgrun 

Then, we execute the database initialization. By binding both directories, we enable postgres to write on the VM.

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif initdb
    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif pg_ctl -D /var/lib/postgresql/data -l logfile start

Then, we can connect to the intial postgres database to check if the setup was successful

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif psql -d postgres

For now, the database setup is complete. We will populate our pointcloud database with data later

#### Project 
Then, we set up our project with

    git clone https://github.com/kdmayer/CS224W_LIDAR.git

During the "git clone" step, you will need to provide your GitHub username and your access token.

Then, we continue the set up of the container with

    cd CS224W_LIDAR && \
    pip install conda-lock

Make sure to add '/home/vagrant/.local/bin' to your $PATH, possibly to your .bashrc

    export PATH=$PATH:/home/vagrant/.local/bin

#### Python environment
We install our conda environment and verify installation
    
    conda-lock install -n cs224w && \
    conda env list

In the shell, we run

    source /usr/local/etc/profile.d/conda.sh && \
    conda activate cs224w

Please note that both commands are needed whenever we connect to the shell of the .sif container with

    singularity shell cs224w.sif


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

### Note:

If you have already created and used the vm-singularity folder for another VM, you will need to destroy the VM and delete the Vagrantfile.

From the vm-singularity folder, execute

    vagrant destroy && \
    rm Vagrantfile

Incomplete and Docker do not run on Sherlock

