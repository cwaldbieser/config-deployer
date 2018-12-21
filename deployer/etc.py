
import os
import sys
from deployer.shellfuncs import shellquote

def copy_etc(conn, config, src_dir='etc', dst_dir='/etc'):
    """
    If the deployed config folder contains a top level folder named
    'etc', its contents are copied to the corresponding locations
    in the /etc file hirearchy.
    """
    remote_config_dir = config.get_remote_config_folder()
    _copy_etc(conn, remote_config_dir, src_dir, dst_dir)

def _copy_etc(conn, parent_dir, src_dir, dst_dir):
    """
    If `parent_dir` contains a top-level folder named , th the value
    in `src_dir`, its contents
    are copied into the corresponding locations
    in the `dst_dir` file hirearchy.
    """
    src_etc = strip_trailing_slash(os.path.join(parent_dir, src_dir))
    dst_dir = strip_trailing_slash(dst_dir)
    inner_cmd = "if [ -d {0} ]; then cp -dR --remove-destination {0}/. {1}/ ; fi".format(shellquote(src_etc), shellquote(dst_dir))
    conn.sudo("bash -c {}".format(shellquote(inner_cmd)))

def strip_trailing_slash(pth):
    """
    Remove the trailing slash from a path.
    """
    return pth.rstrip("/")

