
import os
import sys
from fabric.api import *
from fabric.contrib import console as fabconsole
from fabric import operations
from fabric import utils as fabutils
import yaml
from deployer.archive_filter import filter_files_for_archival 
from deployer import config
from deployer.etc import _copy_etc
from deployer.fabcmdline import yesno2boolean
from deployer.permissions import apply_permissions
from deployer import template_tools as ttools
from deployer.shellfuncs import shellquote

@task
def deploy_config(src_commit=None, move_etc='Y', local_archive=None):
    """
    Deploy a configuration.
    
    :param move_etc:`(Y)/N - Move the embedded 'etc' config to the '/etc' root.` 
    :param local_archive:`Don't deploy-- instead create a local archive at this path.`
    """
    move_etc = yesno2boolean(move_etc)
    if move_etc and (not local_archive is None):
        fabutils.warn("Option `local_archive` will ignore option `move_etc`.")
        move_etc = False
    if local_archive:
        local_archive_folder = os.path.dirname(local_archive)
        if not os.path.isdir(local_archive_folder):
            fabutils.abort("Folder `{}` does not exist.".format(local_archive_folder))
    archive_path = create_local_archive(src_commit)
    if not local_archive is None:
        local("cp {} {}".format(shellquote(archive_path), shellquote(local_archive)))
        sys.exit(0) 
    remote_config_folder = config.get_remote_config_folder() 
    remote_archive = run("mktemp")
    paths = operations.put(archive_path, remote_archive)
    local("rm {0}".format(shellquote(archive_path)))
    remote_stagedir = run("mktemp -d")
    with cd(remote_stagedir):
        run("tar xzvf {0}".format(shellquote(remote_archive)))
        run("rm {0}".format(shellquote(remote_archive)))
        config_owner = config.get_config_owner()
        config_group = config.get_config_group()
        sudo("chown -R {0}:{1} {2}".format(shellquote(config_owner), shellquote(config_group), shellquote(remote_stagedir)))
        folder_perms = config.get_config_folder_perms()
        file_perms = config.get_config_file_perms()
        ad_hoc_perms = config.get_ad_hoc_perms()
        if folder_perms.lower() != "skip":
            sudo("chmod {0} -R {1}".format(folder_perms, shellquote(remote_stagedir)))
        if file_perms.lower() != "skip":
            sudo("find {0} -type f -exec chmod {1} {{}} \;".format(shellquote(remote_stagedir), file_perms))
        for path, perm in ad_hoc_perms.items():
            sudo("chmod {0} {1}".format(shellquote(perm), shellquote(path)))        
    apply_permissions(remote_stagedir)
    if move_etc:
        remote_staged_etc = os.path.join(remote_stagedir, "etc")
        _copy_etc(remote_stagedir, 'etc', '/etc')
        sudo("rm -Rf {0}".format(shellquote(remote_staged_etc)))
    is_docker_build_target = config.is_docker_build_target()
    if is_docker_build_target:
        build_docker_target(remote_stagedir) 
    if not remote_config_folder is None:
        sudo("rm -Rf {0}".format(remote_config_folder))
        sudo("mv {0} {1}".format(remote_stagedir, remote_config_folder))
        with settings(hide('warnings'), warn_only=True):
            result = sudo("which restorecon")
        if not result.failed:
            sudo("restorecon -R {0}".format(shellquote(remote_config_folder)))
    else:
        sudo("rm -Rf {}".format(shellquote(remote_stagedir)))
    
def build_docker_target(remote_stagedir):
    """
    Build a docker image from the configuration in `remote_stagedir`.
    """
    with cd(remote_stagedir):
        build_name = config.get_docker_build_name()
        build_path = config.get_docker_build_path()
        rm_flag = config.get_docker_build_rm()
        build_args = config.get_docker_build_args() 
        args = ['docker', 'build']
        if rm_flag:
            args.append("--rm")
        if not build_name is None:
            args.append("-t")
            args.append(shellquote(build_name))
        for k, v in build_args.items():
            args.append("--build-arg")
            args.append(shellquote("{}={}".format(k, v)))
        args.append(shellquote(build_path))
        command = ' '.join(args)
        sudo(command)

def create_local_archive(src_commit):
    """
    Create local archive and return its path.
    """
    wt = config.get_working_tree()
    if src_commit is None:
        src_branch = config.get_config_branch()
    else:
        src_branch = src_commit
    if not os.path.exists(wt):
        fabutils.abort("Working tree '{0}' does not exist!".format(wt))
    has_secrets = os.path.exists(os.path.join(wt, ".gitsecret")) 
    with lcd(wt):
        with settings(hide('warnings'), warn_only=True):
            result = local("git diff-index --quiet HEAD --", capture=True)
        if result.failed:
            if fabconsole.confirm("There are uncommited changes in the working tree.  Reset to HEAD?"):
                local("git reset --hard HEAD")
            else:
                fabutils.abort("Can't use working tree with uncommitted changes.  Stash, commit, or reset.")
        local("git checkout {0}".format(shellquote(src_branch)))
        if has_secrets:
            local("git secret reveal")
            ttools.fill_templates()
        archive_branch = "{0}-archive".format(src_branch)
        with settings(hide('warnings'), warn_only=True):
            local("git branch -D {0}".format(shellquote(archive_branch))) 
        local("git checkout -b {0}".format(shellquote(archive_branch))) 
        filter_files_for_archival(".secret") 
        filter_files_for_archival(".template") 
        if has_secrets:
            secrets_file_name = config.get_secrets_file_name()
            if secrets_file_name is not None:
                local("git rm -f {0}".format(shellquote(secrets_file_name)))
        if os.path.exists(os.path.join(wt, '.gitignore')):
            local("git rm -f .gitignore")
        if os.path.exists(os.path.join(wt, '.gitsecret')):
            local("git rm -rf .gitsecret")
        with settings(hide('warnings'), warn_only=True):
            local("git commit -m 'Decrypted for deployment.'")
        archive_path = local("mktemp", capture=True)
        local("git archive --format tgz -o {0} HEAD".format(shellquote(archive_path)))
        local("git checkout {0}".format(shellquote(src_branch)))
        local("git branch -D {0}".format(shellquote(archive_branch)))
    return archive_path

