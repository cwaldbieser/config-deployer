
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
