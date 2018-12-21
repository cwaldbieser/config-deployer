
from deployer.shellfuncs import shellquote

def docker_run(conn, config, stop_and_remove=None):
    """
    Run a docker container from a deployed image.
    """
    if stop_and_remove is not None:
        docker_stop(conn, stop_and_remove)
        docker_rm(conn, stop_and_remove)
    build_name = config.get_docker_build_name()
    args = ['docker', 'run']
    args.extend(config.get_docker_run_args())
    args.append(build_name)
    args = [shellquote(arg) for arg in args]
    cmd = ' '.join(args)
    conn.sudo(cmd)

def docker_stop(conn, container):
    """
    Stop a docker container from a deployed image.
    """
    args = ['docker', 'stop']
    args.append(container)
    args = [shellquote(arg) for arg in args]
    cmd = ' '.join(args)
    conn.sudo(cmd)

def docker_rm(conn, container):
    """
    Stop a docker container from a deployed image.
    """
    args = ['docker', 'rm']
    args.append(container)
    args = [shellquote(arg) for arg in args]
    cmd = ' '.join(args)
    conn.sudo(cmd)

