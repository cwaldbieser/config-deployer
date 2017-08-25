
from fabric.api import *
from fabric import operations
from deployer.shellfuncs import shellquote

@task
def install_package(name):
    """
    Deploy RPM path or package name.
    """
    sudo("yum install -y -q -e 0 {0}".format(name))

@task 
def install_local_package(path):
    """
    Copy a local package to the target host and then install it.
    """
    result = sudo("mktemp -d")
    paths = operations.put(path, result, use_sudo=True)
    for remote_path in paths:
        install_package(remote_path)
        sudo("rm -f {0}".format(shellquote(remote_path)))

@task
def remove_package(name):
    """
    Uninstall a package.
    """
    sudo("yum remove -y -q -e 0 {0}".format(name))

