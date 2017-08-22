
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
    with open(CONFIG_PATH, "r") as f:
        CONFIG = yaml.load(f)
    _set_roles()

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
    return CONFIG['working-tree']

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
    return CONFIG['targets']['config-folder']

def get_config_owner():
    """
    Return the owner of the config folder.
    """
    global CONFIG
    return CONFIG['targets'].get('config-owner', 'root')

def get_config_group():
    """
    Return the group of the config folder.
    """
    global CONFIG
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

