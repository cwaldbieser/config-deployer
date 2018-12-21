
from configparser import SafeConfigParser
import os
import sys
import yaml
import attr
from fabric import SerialGroup
from fabric.config import Config as ConnectionConfig
from invoke import Exit

@attr.s
class Config(object):
    settings = attr.ib(default=None)
    stage = attr.ib(default=None)
    conn_pool = attr.ib(default=None)

    def get_config_branch(self):
        """
        Get the branch of the git working tree to use.
        """
        role = self.stage
        branch = self.settings['roles'][role].get('config-branch', role)
        return branch

    def get_working_tree(self):
        """
        Get the working tree URL.
        """
        settings = self.settings
        wt = settings['working-tree']
        if not os.path.exists(wt):
            wt_base = settings.get('working_tree_base', None)
            if wt_base:
                new_wt = os.path.join(
                    wt_base,
                    os.path.basename(wt.rstrip('/'))
                )
                if os.path.exists(new_wt):
                    return new_wt
        return wt

    def get_secrets_file_name(self):
        """
        Return the name of the *secrets* file (`secrets.yml` is the default). 
        """
        return self.settings.get('secrets-file-name', 'secrets.yml')

    def get_remote_config_folder(self):
        """
        Return the path of the config folder on the remote host.
        """
        return self.settings['targets'].get('config-folder', None)

    def get_config_owner(self):
        """
        Return the owner of the config folder.
        """
        settings = self.settings
        role = settings['roles'][self.stage]
        config_owner = role.get("config-owner", None)
        if config_owner is None:
            config_owner = settings['targets'].get('config-owner', 'root') 
        return config_owner

    def get_config_group(self):
        """
        Return the group of the config folder.
        """
        settings = self.settings
        role = settings['roles'][self.stage]
        group = role.get("config-group", None)
        if group is None:
            group = settings['targets'].get('config-group', None)
        if group is None:
            group = self.get_config_owner()
        return group

    def get_config_folder_perms(self):
        """
        Return the permissions of the config folders.
        """
        return self.settings['targets'].get('config-folder-perms', 'u=rx,go=')

    def get_config_file_perms(self):
        """
        Return the permissions of the config folders.
        """
        return self.settings['targets'].get('config-file-perms', 'u=r,go=')

    def get_ad_hoc_perms(self):
        """
        Return the permissions of ad hoc files or folders.
        """
        return self.settings['targets'].get('ad-hoc-perms', {})

    def is_docker_build_target(self):
        """
        Return True is the targets section has `docker-build-target` set.
        """
        targets = self.settings['targets']
        return targets.get('docker-build-target', False)

    def get_docker_build_name(self):
        """
        Return Docker build name or None.
        """
        settings = self.settings
        role = settings['roles'][self.stage]
        return role.get("docker-build-name", None)

    def get_docker_build_path(self):
        """
        Return Docker build path or '.'.
        """
        role = self.settings['roles'][self.stage]
        return role.get("docker-build-path", '.')

    def get_docker_build_rm(self):
        """
        Return whether `rm` option to remove intermediate containers after a
        successful build should be enabled or not.
        """
        role = self.settings['roles'][self.stage]
        return role.get("docker-build-rm", None)
        
    def get_docker_build_args(self):
        """
        Return a dict of Docker build-args for a docker target.
        """
        role = self.settings['roles'][self.stage]
        return dict(role.get("docker-build-args", {}))

    def get_docker_build_options(self):
        """
        Return a list of command line to apply to `docker run`. 
        """
        role = self.settings['roles'][self.stage]
        return list(role.get("docker-build-options", []))

    def get_docker_run_args(self):
        """
        Return a list of args to apply to `docker run`. 
        """
        role = self.settings['roles'][self.stage]
        return list(role.get("docker-run-args", []))


def load_config(config_path, stage):
    """
    Load the deployment config.

    :param:`config_path`: Full or relative path to deployment config file.  May be
        relative to DEPLOYER_CONFIG_PREFIX environment variable. 
    :param:`stage`: The stage (aka role) used to select target hosts.

    :returns: A configuration object.
    """
    cfg = Config()
    cfg.stage = stage
    deployer_config_prefix = os.environ.get('DEPLOYER_CONFIG_PREFIX', None)
    if deployer_config_prefix is not None:
        config_path = os.path.join(deployer_config_prefix, config_path)
    with open(config_path, "r") as f:
        cfg.settings = yaml.load(f)
    if not stage in cfg.settings['roles']:
        raise Exit("Stage `{}` not found in configuration.".format(stage))
    create_connections_(cfg)
    settings = load_settings_()
    if 'working_tree_base' in settings:
        cfg.settings['working_tree_base'] = settings['working_tree_base']
    return cfg

def load_settings_():
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
    scp = SafeConfigParser()
    scp.read(paths)
    if scp.has_section("SOURCES"):
        if scp.has_option("SOURCES", "working_tree_base"):
            settings['working_tree_base'] = os.path.expanduser(scp.get("SOURCES", "working_tree_base"))
    return settings

def create_connections_(cfg):
    """
    Create connections from the config and stage.
    """
    roles = cfg.settings['roles']
    stage = roles[cfg.stage]
    target_hosts = stage['target-hosts']
    cf = ConnectionConfig({'run': {'echo': True, 'env': dict(os.environ)}})
    group = SerialGroup(*target_hosts, config=cf)
    cfg.conn_pool = group

