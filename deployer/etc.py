
import os
from fabric.api import *
from fabric.contrib import console as fabconsole
from fabric import operations
from fabric import utils as fabutils
import deployer.config as config
from deployer.fabcmdline import yesno2boolean
from deployer.shellfuncs import shellquote

@task
def copy_etc(src_dir='etc', dst_dir='/etc'):
    """
    If the deployed config folder contains a top level folder named
    'etc', its contents are copied to the corresponding locations
    in the /etc file hirearchy.
    """
    remote_config_dir = config.get_remote_config_folder()
    src_etc = strip_trailing_slash(os.path.join(remote_config_dir, src_dir))
    dst_dir = strip_trailing_slash(dst_dir)
    sudo("cp -dR {0}/. {1}/".format(shellquote(src_etc), shellquote(dst_dir)))

def strip_trailing_slash(pth):
    """
    Remove the trailing slash from a path.
    """
    return pth.rstrip("/")

