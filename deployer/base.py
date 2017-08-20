
import os
import sys
from fabric.api import *
from fabric.contrib import console as fabconsole
from fabric import operations
from fabric import utils as fabutils
import yaml
from deployer.archive_filter import filter_files_for_archival 
from deployer import config
from deployer.fabcmdline import yesno2boolean
from deployer import template_tools as ttools
from deployer.shellfuncs import shellquote

config.load_config()

@task
def deploy_config():
    """
    Deploy a configuration.
    """
    wt = config.get_working_tree()
    src_branch = config.get_config_branch()
    remote_config_folder = config.get_remote_config_folder() 
    with lcd(wt):
        with settings(hide('warnings'), warn_only=True):
            result = local("git diff-index --quiet HEAD --", capture=True)
        if result.failed:
            if fabconsole.confirm("There are uncommited changes in the working tree.  Reset to HEAD?"):
                local("git reset --hard HEAD")
            else:
                fabutils.abort("Can't use working tree with uncommitted changes.  Stash, commit, or reset.")
        local("git checkout {0}".format(shellquote(src_branch)))
        local("git secret reveal")
        ttools.fill_templates()
        archive_branch = "{0}-archive".format(src_branch)
        with settings(hide('warnings'), warn_only=True):
            local("git branch -D {0}".format(shellquote(archive_branch))) 
        local("git checkout -b {0}".format(shellquote(archive_branch))) 
        filter_files_for_archival(".secret") 
        filter_files_for_archival(".template") 
        secrets_file_name = config.get_secrets_file_name()
        local("git rm -f {0}".format(shellquote(secrets_file_name)))
        local("git rm -f .gitignore")
        local("git rm -rf .gitsecret")
        local("git commit -m 'Decrypted for deployment.'")
        archive_path = local("mktemp", capture=True)
        local("git archive --format tgz -o {0} HEAD".format(shellquote(archive_path)))
        local("git checkout {0}".format(shellquote(src_branch)))
        local("git branch -D {0}".format(shellquote(archive_branch)))
    remote_archive = run("mktemp")
    paths = operations.put(archive_path, remote_archive)
    local("rm {0}".format(shellquote(archive_path)))
    remote_stagedir = run("mktemp -d")
    with cd(remote_stagedir):
        run("tar xzvf {0}".format(shellquote(remote_archive)))
        run("rm {0}".format(shellquote(remote_archive)))
        config_owner = config.get_config_owner()
        sudo("chown -R {0} {1}".format(shellquote(config_owner), shellquote(remote_stagedir)))
        config_perms = config.get_config_perms()
        sudo("chmod {0} -R {1}".format(config_perms, shellquote(remote_stagedir)))
        sudo("rm -Rf {0}".format(remote_config_folder))
        sudo("mv {0} {1}".format(remote_stagedir, remote_config_folder))
    
    
