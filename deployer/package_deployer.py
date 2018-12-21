
from deployer.shellfuncs import shellquote

def install_rpm(conn, name):
    """
    Deploy RPM path or package name.
    """
    conn.sudo("yum install -y -q -e 0 {}".format(name))

def install_local_rpm(conn, path):
    """
    Copy a local package to the target host and then install it.
    """
    remote_path = conn.run("mktemp").stdout.rstrip()
    conn.put(path, remote_path)
    install_rpm(conn, remote_path)
    conn.run("rm -f {}".format(shellquote(remote_path)))

def remove_rpm(conn, name):
    """
    Uninstall a package.
    """
    conn.sudo("yum remove -y -q -e 0 {}".format(name))

