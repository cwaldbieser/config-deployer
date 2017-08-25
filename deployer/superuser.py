
from fabric.api import *

@task
def root_cmd(cmd):
    """
    Issue arbitrary commands as the super user.
    
    WARNING: Quoting will be resolved 2 times.  Once when args are passed to
    `fab` and again when passed to the remote shell!
    """
    sudo(cmd) 

