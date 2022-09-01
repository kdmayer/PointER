## Setup Instructions

Clone repo to your local machine. Navigate into the root directory.

In your conda base environment, follow the subsequent steps:

    pip install conda-lock 
    conda-lock -f environment.yml 
    conda-lock install [-p {prefix}|-n {name}]
    
Example: 

    conda-lock install -p win-64 -n cs224w 

Note: The -n argument will overwrite the name specified in the environment.yml file

Then, activate your environment with:

    conda activate cs224w

You are ready to go.

Note:

- If you need to add new **conda** core dependencies, adapt the environment.yml file manually and go through the same process.
- If you need to add new **pip** core dependencies, install them manually after going through the set up with conda-lock.

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

