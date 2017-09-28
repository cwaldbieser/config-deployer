
from __future__ import print_function
from fabric.api import *
from fabric.contrib import console as fabconsole
from fabric.decorators import (
    runs_once
)
from fabric import operations
from fabric import utils as fabutils
import deployer.config as config

@task
@runs_once
def list_roles():
    """
    List all the roles and host mappings for a configuration.
    """
    global env
    fmt = "{:14}: {}"
    for role, hosts in env.roledefs.items():
        leading = role
        for n, host in enumerate(hosts):
            if n != 0:
                leading = ""
            print(fmt.format(leading, host))
        print("")

