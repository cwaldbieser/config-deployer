
from fabric.api import *
from fabric.contrib import console as fabconsole
from fabric import operations
from fabric import utils as fabutils
from deployer.fabcmdline import yesno2boolean

@task
def restart_httpd(hard='n'):
    """
    Restart the web server.  Graceful by default.
    Hard if required.
    """
    hard = yesno2boolean(hard)
    sudo("apachectl -t")
    if hard:
        sudo("systemctl restart httpd")
    else:
        sudo("apachectl graceful")

