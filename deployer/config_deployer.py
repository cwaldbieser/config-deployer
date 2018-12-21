
import os
import sys
import yaml
from invoke import Exit
from invocations.console import confirm
from deployer.archive_filter import filter_files_for_archival 
from deployer.etc import _copy_etc
from deployer.permissions import apply_permissions
from deployer import template_tools as ttools
from deployer.shellfuncs import shellquote
from deployer.terminal import warn

def deploy_config(conn, config, src_commit=None, move_etc=True, local_archive=None):
    """
    Deploy a configuration.
    
    :param move_etc:`(True)/False - Move the embedded 'etc' config to the '/etc' root.` 
    :param local_archive:`Don't deploy-- instead create a local archive at this path.`
    """
    if move_etc and (not local_archive is None):
        warn("Option `local_archive` will ignore option `move_etc`.")
        move_etc = False
    if local_archive:
        local_archive_folder = os.path.dirname(local_archive)
        if not os.path.isdir(local_archive_folder):
            raise Exit("Folder `{}` does not exist.".format(local_archive_folder))
    archive_path = create_local_archive(conn, config, src_commit)
    if not local_archive is None:
        conn.local("cp {} {}".format(shellquote(archive_path), shellquote(local_archive)))
        sys.exit(0) 
    remote_config_folder = config.get_remote_config_folder() 
    remote_archive = conn.run("mktemp").stdout.rstrip()
    paths = conn.put(archive_path, remote_archive)
    conn.local("rm {}".format(shellquote(archive_path)))
    remote_stagedir = conn.run("mktemp -d").stdout.rstrip()
    with conn.cd(remote_stagedir):
        conn.run("tar xzvf {}".format(shellquote(remote_archive)))
        conn.run("rm {}".format(shellquote(remote_archive)))
    config_owner = config.get_config_owner()
    config_group = config.get_config_group()
    conn.sudo("chown -R {}:{} {}".format(shellquote(config_owner), shellquote(config_group), shellquote(remote_stagedir)))
    folder_perms = config.get_config_folder_perms()
    file_perms = config.get_config_file_perms()
    ad_hoc_perms = config.get_ad_hoc_perms()
    if folder_perms.lower() != "skip":
        conn.sudo("chmod {} -R {}".format(folder_perms, shellquote(remote_stagedir)))
    if file_perms.lower() != "skip":
        conn.sudo("find {} -type f -exec chmod {} {{}} \;".format(shellquote(remote_stagedir), file_perms))
    for path, perm in ad_hoc_perms.items():
        conn.sudo("chmod {} {}".format(shellquote(perm), shellquote(path)))        
    apply_permissions(conn, config, remote_stagedir)
    if move_etc:
        remote_staged_etc = os.path.join(remote_stagedir, "etc")
        _copy_etc(conn, remote_stagedir, 'etc', '/etc')
        conn.sudo("rm -Rf {}".format(shellquote(remote_staged_etc)))
    is_docker_build_target = config.is_docker_build_target()
    if is_docker_build_target:
        build_docker_target(conn, config, remote_stagedir) 
    if not remote_config_folder is None:
        conn.sudo("rm -Rf {}".format(remote_config_folder))
        conn.sudo("mv {} {}".format(remote_stagedir, remote_config_folder))
        result = conn.sudo("which restorecon", warn=True)
        if not result.failed:
            conn.sudo("restorecon -R {}".format(shellquote(remote_config_folder)))
    else:
        conn.sudo("rm -Rf {}".format(shellquote(remote_stagedir)))
    
def build_docker_target(conn, config, remote_stagedir):
    """
    Build a docker image from the configuration in `remote_stagedir`.
    """
    with conn.cd(remote_stagedir):
        build_name = config.get_docker_build_name()
        build_path = config.get_docker_build_path()
        rm_flag = config.get_docker_build_rm()
        build_args = config.get_docker_build_args() 
        build_options = config.get_docker_build_options()
        args = ['docker', 'build']
        if rm_flag:
            args.append("--rm")
        if not build_name is None:
            args.append("-t")
            args.append(shellquote(build_name))
        for k, v in build_args.items():
            args.append("--build-arg")
            args.append(shellquote("{}={}".format(k, v)))
        args.extend(build_options)
        args.append(shellquote(build_path))
        command = ' '.join(args)
    conn.sudo('''bash -c "cd {} && {}"'''.format(shellquote(remote_stagedir), command))

def create_local_archive(conn, config, src_commit):
    """
    Create local archive and return its path.
    """
    wt = config.get_working_tree()
    if src_commit is None:
        src_branch = config.get_config_branch()
    else:
        src_branch = src_commit
    if not os.path.exists(wt):
        raise Exit("Working tree '{}' does not exist!".format(wt))
    has_secrets = os.path.exists(os.path.join(wt, ".gitsecret")) 
    result = conn.local("cd {} && git diff-index --quiet HEAD --".format(shellquote(wt)), warn=True)
    if result.failed:
        if confirm("There are uncommited changes in the working tree.  Reset to HEAD?"):
            conn.local("cd {} && git reset --hard HEAD".format(shellquote(wt)))
        else:
            raise Exit("Can't use working tree with uncommitted changes.  Stash, commit, or reset.")
    conn.local("cd {} && git checkout {}".format(shellquote(wt), shellquote(src_branch)))
    if has_secrets:
        conn.local("cd {} && git secret reveal".format(wt))
        ttools.fill_templates(config)
    archive_branch = "{}-archive".format(src_branch)
    conn.local("cd {} && git branch -D {}".format(shellquote(wt), shellquote(archive_branch)), warn=True) 
    conn.local("cd {} && git checkout -b {}".format(shellquote(wt), shellquote(archive_branch))) 
    filter_files_for_archival(conn, config, ".secret") 
    filter_files_for_archival(conn, config, ".template") 
    if has_secrets:
        secrets_file_name = config.get_secrets_file_name()
        if secrets_file_name is not None:
            conn.local("cd {} && git rm -f {}".format(shellquote(wt), shellquote(secrets_file_name)))
    if os.path.exists(os.path.join(wt, '.gitignore')):
        conn.local("cd {} && git rm -f .gitignore".format(shellquote(wt)))
    if os.path.exists(os.path.join(wt, '.gitsecret')):
        conn.local("cd {} && git rm -rf .gitsecret".format(shellquote(wt)))
    conn.local("cd {} && git commit -m 'Decrypted for deployment.'".format(shellquote(wt)), warn=True)
    archive_path = conn.local("cd {} && mktemp".format(shellquote(wt))).stdout.rstrip()
    conn.local("cd {} && git archive --format tgz -o {} HEAD".format(shellquote(wt), shellquote(archive_path)))
    conn.local("cd {} && git checkout {}".format(shellquote(wt), shellquote(src_branch)))
    conn.local("cd {} && git branch -D {}".format(shellquote(wt), shellquote(archive_branch)))
    return archive_path

