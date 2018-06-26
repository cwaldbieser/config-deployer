
import ConfigParser
import os
import sys
from fabric.api import env
from fabric import utils as fabutils
import yaml

CONFIG_PATH = None
CONFIG = None

if not 'DEPLOYER_CONFIG' in os.environ:
    fabutils.abort("Set the environment variable 'DEPLOYER_CONFIG' to a deployment configuration file.")

def load_config():
    """
    Load the deployment config.
    """
    global CONFIG_PATH
    global CONFIG
    CONFIG_PATH = os.environ['DEPLOYER_CONFIG']
    deployer_config_prefix = os.environ.get('DEPLOYER_CONFIG_PREFIX', None)
    if deployer_config_prefix is not None:
        CONFIG_PATH = os.path.join(deployer_config_prefix, CONFIG_PATH)
    with open(CONFIG_PATH, "r") as f:
        CONFIG = yaml.load(f)
    _set_roles()
    settings = _load_settings()
    if 'working_tree_base' in settings:
        CONFIG['working_tree_base'] = settings['working_tree_base']

def _load_settings():
    """
    Load settings that may affect the deployment from standard locations:

    ~/.deployer.cfg

    Returns a mapping on settings.
    """
    settings = {}
    paths = []
    user_settings = os.path.expanduser('~/.deployer.cfg')
    if os.path.exists(user_settings):
        paths.append(user_settings)
    scp = ConfigParser.SafeConfigParser()
    scp.read(paths)
    if scp.has_section("SOURCES"):
        if scp.has_option("SOURCES", "working_tree_base"):
            settings['working_tree_base'] = os.path.expanduser(scp.get("SOURCES", "working_tree_base"))
    return settings

def _set_roles():
    """
    Set the environment roles from the deployment config file.
    """
    global env
    global CONFIG
    roles = CONFIG['roles']
    env_roles = {}
    for role, values in roles.items():
        hosts = list(values['target-hosts'])
        env_roles[role] = hosts
    env.roledefs = env_roles

def get_primary_role():
    """
    Get the highest priority role of a host being processed.
    """
    global env, CONFIG
    roles = list(env.effective_roles)
    if len(roles) > 0:
        priorities = []
        for role in roles:
            role_info = CONFIG['roles'][role]
            priority = role_info.get('priority', 0)    
            priorities.append((priority, role))
        priorities.sort()
        roles = [r for (p, r) in priorities]
    role = env.effective_roles[0]
    return role

def get_config_branch():
    """
    Get the branch of the git working tree to use.
    """
    global env, CONFIG
    role = get_primary_role()
    branch = CONFIG['roles'][role].get('config-branch', role)
    return branch

def get_working_tree():
    """
    Get the working tree URL.
    """
    global CONFIG
    wt = CONFIG['working-tree']
    if not os.path.exists(wt):
        wt_base = CONFIG.get('working_tree_base', None)
        if wt_base:
            new_wt = os.path.join(
                wt_base,
                os.path.basename(wt.rstrip('/'))
            )
            if os.path.exists(new_wt):
                return new_wt
    return wt

def get_secrets_file_name():
    """
    Return the name of the *secrets* file (`secrets.yml` is the default). 
    """
    global CONFIG
    return CONFIG.get('secrets-file-name', 'secrets.yml')

def get_remote_config_folder():
    """
    Return the path of the config folder on the remote host.
    """
    global CONFIG
    return CONFIG['targets'].get('config-folder', None)

def get_config_owner():
    """
    Return the owner of the config folder.
    """
    global CONFIG
    primary_role_name = get_primary_role()
    primary_role = CONFIG['roles'][primary_role_name]
    config_owner = primary_role.get("config-owner", None)
    if config_owner is None:
        config_owner = CONFIG['targets'].get('config-owner', 'root') 
    return config_owner

def get_config_group():
    """
    Return the group of the config folder.
    """
    global CONFIG
    primary_role_name = get_primary_role()
    primary_role = CONFIG['roles'][primary_role_name]
    group = primary_role.get("config-group", None)
    if group is None:
        group = CONFIG['targets'].get('config-group', None)
    if group is None:
        group = get_config_owner()
    return group

def get_config_folder_perms():
    """
    Return the permissions of the config folders.
    """
    global CONFIG
    return CONFIG['targets'].get('config-folder-perms', 'u=rx,go=')

def get_config_file_perms():
    """
    Return the permissions of the config folders.
    """
    global CONFIG
    return CONFIG['targets'].get('config-file-perms', 'u=r,go=')

def get_ad_hoc_perms():
    """
    Return the permissions of ad hoc files or folders.
    """
    global CONFIG
    return CONFIG['targets'].get('ad-hoc-perms', {})

def is_docker_build_target():
    """
    Return True is the targets section has `docker-build-target` set.
    """
    global CONFIG
    targets = CONFIG['targets']
    return targets.get('docker-build-target', False)

def get_docker_build_name():
    """
    Return Docker build name or None.
    """
    global CONFIG
    primary_role_name = get_primary_role()
    primary_role = CONFIG['roles'][primary_role_name]
    return primary_role.get("docker-build-name", None)

def get_docker_build_path():
    """
    Return Docker build path or '.'.
    """
    global CONFIG
    primary_role_name = get_primary_role()
    primary_role = CONFIG['roles'][primary_role_name]
    return primary_role.get("docker-build-path", '.')

def get_docker_build_rm():
    """
    Return whether `rm` option to remove intermediate containers after a
    successful build should be enabled or not.
    """
    global CONFIG
    primary_role_name = get_primary_role()
    primary_role = CONFIG['roles'][primary_role_name]
    return primary_role.get("docker-build-rm", None)
    
def get_docker_build_args():
    """
    Return a dict of Docker build-args for a docker target.
    """
    global CONFIG
    primary_role_name = get_primary_role()
    primary_role = CONFIG['roles'][primary_role_name]
    return dict(primary_role.get("docker-build-args", {}))

def get_docker_run_args():
    """
    Return a list of args to apply to `docker run`. 
    """
    global CONFIG
    primary_role_name = get_primary_role()
    primary_role = CONFIG['roles'][primary_role_name]
    return list(primary_role.get("docker-run-args", []))
