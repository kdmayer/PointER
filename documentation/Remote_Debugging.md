In order to debug the code, we need to sync the PyCharm interpreter with our custom conda environment on the vagrant vm.

In your vm-singularity folder, run 

    vagrant ssh-config > vagrant-ssh

The resulting vagrant-ssh file will look like this 

    Host default 
      HostName 127.0.0.1 
      User vagrant 
      Port 2222 
      UserKnownHostsFile /dev/null 
      StrictHostKeyChecking no 
      PasswordAuthentication no 
      IdentityFile PATH_TO_PRIVATE_KEY
      IdentitiesOnly yes 
      LogLevel FATAL

and contain all the necessary information to connect to your vagrant vm via ssh.

In PyCharm, go to 

![](https://github.com/kdmayer/CS224W_LIDAR/blob/main/assets/images/ssh_interpreter.png)

