## Containerized DB setup with extensions

### Singularity Setup:

Go to the [Singularity Docs](https://docs.sylabs.io/guides/3.0/user-guide/installation.html#install-on-windows-or-mac) and install Singularity.

From the respective Singularity folder, here vm-singularity, start the Virtual Machine with

    export VM=sylabs/singularity-3.0-ubuntu-bionic64 && \
    vagrant init $VM

Install the vagrant-disksize plugin with

    VAGRANT_DISABLE_STRICT_DEPENDENCY_ENFORCEMENT=1 vagrant plugin install vagrant-disksize

And specify the desired disk size in the Vagrantfile

    vagrant.configure('2') do |config|
        config.disksize.size = '50GB'
    end

Afterwards, spin up the virtual machine with

    vagrant up && \
    vagrant ssh

In the VM, create an empty container definition file

    touch cs224w.def

Install vim to manipulate file 

    sudo apt-get update && \
    sudo apt install vim

Copy the container definition file from this repo, i.e. cs224w.def, into your empty .def file in the VM

Build the .sif image from .def in the VM with

    sudo singularity build cs224w.sif cs224w.def

Once the build process has finished, use the cs224w.sif image to open a shell within the container

    singularity shell cs224w.sif

In the .sif container, set up your project with

    git clone https://github.com/kdmayer/CS224W_LIDAR.git

During the "git clone" step, you will need to provide your GitHub username and your access token.

Then, continue the set up of the container with

    cd CS224W_LIDAR && \
    pip install conda-lock

Make sure to add '/home/vagrant/.local/bin' to your $PATH, possibly to your .bashrc

    export PATH=$PATH:/home/vagrant/.local/bin

Install your conda environment and verify installation
    
    conda-lock install -n cs224w && \
    conda env list

In your shell, run

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

### Note:

If you have already created and used the vm-singularity folder for another VM, you will need to destroy the VM and delete the Vagrantfile.

From the vm-singularity folder, execute

    vagrant destroy && \
    rm Vagrantfile

### Incomplete and Docker does not run on Sherlock

### Docker Setup 

Download the latest pgPointcloud Docker image 

    docker pull pgpointcloud/pointcloud

Start the new container with

    docker run --name pgpointcloud -e POSTGRES_DB=cs224w_db -e POSTGRES_PASSWORD=your_personal_password -d pgpointcloud/pointcloud

Check installation and the extensions with

    docker exec -it pgpointcloud psql -U postgres -d cs224w_db -c "\dx"

TODO: 

- Pull GitHub repo
- Install conda environment
- Set docker container as PyCharm interpreter
    