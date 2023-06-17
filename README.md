## Setup Instructions

### Install given conda environment

Clone the GitHub repository to your local machine. Navigate into the root directory.

In your conda base environment, install your environment with 

    conda-lock install [-p {prefix}|-n {name}]

Note: 

- The -p argument specifies your local OS and can be either *linux-64*, *osx-64*, or *win-64*
- The -n argument will overwrite the name specified in the environment.yml file

Example: 

    conda-lock install -n cs224w

Then, activate your environment with:

    conda activate cs224w

You are ready to go.

### Adapt given conda environment

If you need to add new **conda** core dependencies to the existing environment.yml, adapt the environment.yml file manually.

Afterwards,

    pip install conda-lock 
    conda-lock -f environment.yml 
    conda-lock install [-p {prefix}|-n {name}]

If you need to add new **pip** core dependencies, install them manually after going through the set up with conda-lock.

Example:

    pip install <new_core_dependency>


## Exemplary PDAL Output from Point_Cloud_Demo.ipynb
 
 ![PDAL Output](https://github.com/kdmayer/CS224W_LIDAR/blob/main/assets/images/example.png)
 


