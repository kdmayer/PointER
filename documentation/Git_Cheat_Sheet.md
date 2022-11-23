### Setting Git credentials for local repo

When pushing from a remote, such as the VM, we want to authenticate our commits with our registered GitHub account.

To do so, set your credentials in the command line with the following commands:

    git config [--global] user.name "Full Name"
    git config [--global] user.email "email@address.com"

### Print Git history in terminal

    git log --graph --oneline

