
import os
import sys
from deployer.shellfuncs import shellquote
from deployer.terminal import warn

def apply_permissions(conn, config, folder, perm_file='__perms__'):
    """
    Descend recursively into each folder starting with `folder`.
    Look for a file with a name that matches the value of `perm_file`.
    Parse the permission file and apply the permissions to files in
    the folder as applicable.
    """
    result = conn.sudo("find {} -name {} -print".format(shellquote(folder), shellquote(perm_file)))
    lines = result.stdout.splitlines()
    for line in lines:
        if line == '[sudo] password: ':
            continue
        if line.strip() == "":
            continue
        dirpth = os.path.dirname(line)
        for fname, user, group, perms in parse_fields(conn, line):
            pth = os.path.join(dirpth, fname)
            conn.sudo("chown {}:{} {}".format(shellquote(user), shellquote(group), shellquote(pth)))
            conn.sudo("chmod {} {}".format(shellquote(perms), shellquote(pth)))
        conn.sudo("rm -f {}".format(line))

def parse_fields(conn, perm_file):
    """
    Parse the fields of a permissions file.
    Yield each permission.
    """
    result = conn.sudo("cat {}".format(shellquote(perm_file)))
    lines = result.stdout.splitlines()
    for line in lines:
        if line.strip() == "":
            continue
        if line.strip().startswith("#"):
            continue
        fields = line.split(":")
        if len(fields) != 4:
            warn("Permission '{}' in file {} is mal-formed.".format(line, perm_file))
            continue 
        fname = fields[0]
        user = fields[1]
        group = fields[2]
        perms = fields[3]
        yield (fname, user, group, perms)

