
from fabric.api import *
from deployer import config
from deployer.shellfuncs import shellquote

@task
def docker_run():
    """
    Run a docker container from a deployed image.
    """
    build_name = config.get_docker_build_name()
    args = ['docker', 'run']
    args.extend(config.get_docker_run_args())
    args.append(build_name)
    args = [shellquote(arg) for arg in args]
    cmd = ' '.join(args)
    sudo(cmd)

@task
def docker_stop(container):
    """
    Stop a docker container from a deployed image.
    """
    args = ['docker', 'stop']
    args.append(container)
    args = [shellquote(arg) for arg in args]
    cmd = ' '.join(args)
    sudo(cmd)

@task
def docker_rm(container):
    """
    Stop a docker container from a deployed image.
    """
    args = ['docker', 'rm']
    args.append(container)
    args = [shellquote(arg) for arg in args]
    cmd = ' '.join(args)
    sudo(cmd)
