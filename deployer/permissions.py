
import os
from fabric.api import *
from fabric.contrib import console as fabconsole
from fabric import operations
from fabric import utils as fabutils
import deployer.config as config
from deployer.fabcmdline import yesno2boolean
from deployer.shellfuncs import shellquote

@task
def apply_permissions(folder, perm_file='__perms__'):
    """
    Descend recursively into each folder starting with `folder`.
    Look for a file with a name that matches the value of `perm_file`.
    Parse the permission file and apply the permissions to files in
    the folder as applicable.
    """
    result = sudo("find {0} -name {1} -print".format(shellquote(folder), shellquote(perm_file)))
    lines = result.splitlines()
    for line in lines:
        if line.strip() == "":
            continue
        dirpth = os.path.dirname(line)
        for fname, user, group, perms in parse_fields(line):
            pth = os.path.join(dirpth, fname)
            sudo("chown {0}:{1} {2}".format(shellquote(user), shellquote(group), shellquote(pth)))
            sudo("chmod {0} {1}".format(shellquote(perms), shellquote(pth)))
        sudo("rm -f {0}".format(line))

def parse_fields(perm_file):
    """
    Parse the fields of a permissions file.
    Yield each permission.
    """
    result = sudo("cat {0}".format(shellquote(perm_file)))
    lines = result.splitlines()
    for line in lines:
        if line.strip() == "":
            continue
        if line.strip().startswith("#"):
            continue
        fields = line.split(":")
        if len(fields) != 4:
            fabutils.warn("Permission '{0}' in file {1} is mal-formed.".format(line, perm_file))
            continue 
        fname = fields[0]
        user = fields[1]
        group = fields[2]
        perms = fields[3]
        yield (fname, user, group, perms)

