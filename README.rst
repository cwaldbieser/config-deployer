
============================
Tools for Deploying Software
============================

Based on the python Fabric tool.

Example::

    [waldbiec@my-workstation]$ pipenv run ./deploy.py amqp_provisioners-config.yml local deploy-config

The deployment tools assumes a basic structure for the deployment configuration
file.  It also assumes some other conventions unless you tell it otherwise in
order to make configuring a deployment as simple as possible.

-----------------------
Deployment Config Files
-----------------------

The deployment of each application varies a bit from app to app.  As such, 
there is some essential information that needs to be conveyed to the deployment
tools so that it knows what to do with the software configuration and artifacts.

A deployment configuration file is a YAML file with a particular structure.

.. code-block:: yaml

    working-tree: /path/to/working/tree/myapp
    config-folder-perms: u=rx,go=   # Optional (default u=rx,go=)
    config-file-perms: u=r,go=      # Optional (default u=r,go=)
    secrets-file-name: secrets.yml  # Optional (default :file:`secrets.yml`)
    targets:
        config-folder: /etc/myapp
        config-owner: apache        # Optional (default root)
        config-group: apache        # Optional (default same as config-owner)
    roles:
        # Role names are arbitrary.  However, if you use the same names
        # for your repository branches, you don't need to specify the
        # branches explicitly.  Roles are also known as "stages".
        dev:
            config-branch: dev      # If not specified, assumes same name as role.
            # A role priority is an integer and may be negative (low priority) or
            # positive (high priority).  If unspecified, it is assumed to be 0.
            # The priority is used if a host has multiple effective roles, but
            # a single role must be used to perform some mapping (e.g. the 
            # source branch to use).  The highest priority role will be used.
            priority: 0             
            # Target hosts is just a list of all the hosts on which the 
            # configuration should be deployed.
            target-hosts:
                - host1.dev.example.org
                - host2.dev.example.org
                - host3.dev.example.org
        stage:
            target-hosts:
                - host1.stage.example.org
                - host2.stage.example.org
                - host3.stage.example.org
        prod:
            target-hosts:
                - host1.example.org
                - host2.example.org
                - host3.example.org

------------------------
Deploying Configurations
------------------------

The structure of the git repository that holds the application configuration
must have some specific scaffolding.

First, it is assumed that the configuration will have some properties that are
sensitive and should *not* be stored in the repository in clear text.  In order
to keep these secret bits secret, the `git secret <http://git-secret.io/>`_ 
tool is used to encrypt the secrets with symetric encryption ala GnuPG.

Because encrypting a file essentially removes some of the benefits of version
control, actual configuration files that would normally contain secrets in 
clear text are replaced with template files.  The templates use the 
`Jinja2 <http://jinja.pocoo.org/docs/2.9/>`_ template syntax.  Placeholders
are replaced with decrypted secrets at deployment time.

All the secrets for the configuration are placed in a single file in the root
of the project called `secrets.yml`.  This file should be encrypted with 
`git secret`.  This means that all the secrets will be encrypted, and version
history will tell you if *something* in the secrets file changed, but you will
not be able to know exactly what changed unless you keep notes in the commit 
message.

.. note::

    Secrets that are their own files (e.g. private key files) can be encrypted
    independently of the `secrets.yml` file.  `secrets.yml` should be used only
    for secrets that would otherwise require encrypting non-secret 
    configuration in order to be protected.

The structure of `secrets.yml` looks like:

.. code:: yaml

    # Individual templates should be listed under the *files* key.
    files:
        app-config-w-secrets.cfg.template:
            secrets:
                ldap_bind: LD4p$3cret 
                mysql_passwd: DB$3kr3t!
        subfolder/another.template:
            secrets:
                web_service_passwd: 4P1$3cr3t

Each template file listed will have its placeholders replaced with the mappings
under its *secrets* key.

--------------------------------------------
Environment Variables and User Configuration
--------------------------------------------

The deployer software looks for configuration in the following locations:

* ~/.deployer.cfg

A number of environment variables control the operation of the software:

* `DEPLOYER_CONFIG_PREFIX` - This specifies a path that will be the prefix for
  your deployment files.  This is useful if you store them under a common
  folder.  You can set this environment variable is your shell startup script,
  e.g. `~/.bashrc`.

""""""""""""""""""""""""""
Set your working tree base
""""""""""""""""""""""""""

If you have many configurations, it is sometimes convenient to arrange them
under a common folder.  This folder may vary if you switch workstations or
just choose to re-organize.  Rather than having to update all your deployment
files, you can specify a working tree base in the deployer configuration:

.. code:: ini

    [SOURCES]
    working_tree_base = ~/git-repos/app_configs

Tilda expansion is supported.

----------------------------------
Deploying to a Docker-Build Target
----------------------------------

Rather than deploying configurations to a physical or virtual machine, it may
be desireable to deploy a configuration as part of a docker image.  In this
kind of deployment, the repository will contain a 
`Dockerfile <https://docs.docker.com/engine/reference/builder/>`_ and supporting
configuration files for building a docker image.  The configuration will have
secrets interpolated prior to executing the dockerfile.  The docker image may
be built on the local host or on a remote host.  Settings can influence the
docker build:

.. code:: yaml

    working-tree: /path/to/repo/containing/Dockerfile
    targets:
        # Indicate that this deployment has a docker-build target.
        docker-build-target: True
    roles:
        stage:
            target-hosts:
                - localhost
            # The built image can be named for later use with `docker run`.
            docker-build-name: shib-idp-tier
            # Values can be supplied from the command line for values in the Dockerfile recipie.
            docker-build-args:
                SHBCFG: ./shib-config/conf
                SHBCREDS: ./shib-config/credentials
                SHBMSGS: ./shib-config/messages
                SHBMD: ./shib-config/metadata
                SHBEDWAPP: ./shib-config/edit-webapp
            # Remove intermediate images (same as `docker build --rm`).
            docker-build-rm: True
            # The docker build path.
            docker-build-path: .

