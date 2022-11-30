### PyCharm Remote Development

Before we can start PyCharm's *Remote Development* tool, we need to navigate to the vm-singularity folder and spin up the VM:

    vagrant up && \
    vagrant ssh

To execute and debug the code on the VM, we use PyCharm's *Remote Development* tool:

    File > Remote Development > SSH > New Connection > 
    Select "vagrant@127.0.0.1:2222 key" > Check Connection and Continue > 
    Select Project Directory as "/home/vagrant/CS224W_LIDAR" > Start IDE and Connect

To add our custom conda environment as the project interpreter on the newly started VM instance:

    JetBrains Client > Preferences > Python Interpreter > Add Interpreter >
    Add Local Interpreter > Select "System Interpreter" > Specify "/home/vagrant/.conda/envs/cs224w/bin/python3.9"

Before we can run any code, we need to establish the connection to our postgres database. From the "/home/vagrant" directory run:

    singularity exec -B $HOME/pgdata:/var/lib/postgresql/data,$HOME/pgrun:/var/run/postgresql cs224w.sif pg_ctl -D /var/lib/postgresql/data -l logfile start

### VM Settings

If you are unsure about your VM's settings, navigate into your *vm-singularity* folder and run 

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

and contain all the necessary information to connect to your vagrant VM.

