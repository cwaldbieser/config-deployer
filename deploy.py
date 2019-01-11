#! /usr/bin/env python

import argparse
import getpass
import sys
from deployer.config import load_config
from deployer import config_deployer
from deployer import docker
from deployer import introspect
from deployer import package_deployer
from deployer.shellfuncs import shellquote

def print_host_banner(conn):
    """
    Print the host banner.
    """
    msg = "=== [Connected to {}] ===".format(conn.host)
    border = "=" * len(msg)
    print()
    print(border)
    print(msg)
    print(border)
    print()

def filter_conn_pool(pool, excluded_hosts):
    """
    Only produce connections that haven't been excluded.
    """
    for conn in pool:
        if conn.host in excluded_hosts:
            continue
        yield conn

def deploy_config(args):
    """
    Deploy a configuration.
    """
    cfg = load_config(args.config, args.stage, args.sudo_passwd, args.pty)
    invoker = cfg.invoker
    archive_path = config_deployer.create_local_archive(invoker, cfg, args.commit)
    if not args.archive is None:
        invoker.run("mv {} {}".format(shellquote(archive_path), shellquote(args.archive)))
    try:
        pool = filter_conn_pool(cfg.conn_pool, set(args.exclude_host))
        for conn in pool:
            print_host_banner(conn)
            config_deployer.deploy_config(
                conn,
                cfg,
                archive_path,
                move_etc=(not args.no_etc) and (args.archive is None))
    finally:
        invoker.run("rm {}".format(shellquote(archive_path)))

def query(args):
    """
    Interrogate runtime configuration.
    """
    cfg = load_config(args.config, args.stage, args.sudo_passwd, args.pty)
    introspect.list_hosts(cfg)

def docker_run(args):
    """
    Run a docker container on remote hosts.
    """
    cfg = load_config(args.config, args.stage, args.sudo_passwd, args.pty)
    pool = filter_conn_pool(cfg.conn_pool, set(args.exclude_host))
    for conn in pool:
        print_host_banner(conn)
        docker.docker_run(conn, cfg, args.stop_and_remove)

def manage_rpm(args):
    """
    Manage RPM packages on remote hosts.
    """
    cfg = load_config(args.config, args.stage, args.sudo_passwd, args.pty)
    pool = filter_conn_pool(cfg.conn_pool, set(args.exclude_host))
    for conn in pool:
        print_host_banner(conn)
        if args.local:
            package_deployer.install_local_rpm(conn, args.package)
        elif args.uninstall:
            package_deployer.remove_rpm(conn, args.package)
        else:
            package_deployer.install_rpm(conn, args.package)

def execute_shell(args):
    """
    Execute arbitrary remote commands.
    """
    cfg = load_config(args.config, args.stage, args.sudo_passwd, args.pty)
    cmd = ' '.join([shellquote(arg) for arg in args.arg])
    pool = filter_conn_pool(cfg.conn_pool, set(args.exclude_host))
    for conn in pool:
        print_host_banner(conn)
        if args.sudo:
            conn.sudo(cmd)
        else:
            conn.run(cmd)

def main(args):
    """
    Main function.
    """
    if not 'func' in args:
        print("Invalid command.", file=sys.stderr)
        sys.exit(1)
    if args.prompt_sudo:
        args.sudo_passwd = getpass.getpass("Enter `sudo` password: ")
    args.func(args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Deploy configurations to remote hosts.")
    parser.add_argument(
        "config",
        action="store",
        help="The name of the configuration")
    parser.add_argument(
        "stage",
        action="store",
        help="The stage to activate.")
    parser.add_argument(
        "--prompt-sudo",
        action="store_true",
        help="Prompt for a `sudo` password that will be used with any invokations of `sudo`.")
    parser.add_argument(
        "-x",
        "--exclude-host",
        action="append",
        metavar="HOST",
        default=[],
        help="Exclude host HOST.  May be used multiple times.")
    parser.add_argument(
        "--pty",
        action='store_true',
        help="When issuing remote commands use a PTY.")
    parser.set_defaults(sudo_passwd=None)
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_dc = subparsers.add_parser('deploy-config', help='Deploy a configuration.')
    parser_dc.add_argument(
        "-c",
        "--commit",
        action="store",
        help="Deploy from the given commit instead of HEAD.")
    parser_dc.add_argument(
        "--archive",
        action="store",
        metavar="path",
        help="Don't deploy.  Instead, create a local archive at PATH.")
    parser_dc.add_argument(
        "--no-etc",
        action="store_true",
        help="Don't deploy the `etc` configuration.")
    parser_dc.set_defaults(func=deploy_config)

    parser_query = subparsers.add_parser('query', help='Interrogate configuration.')
    parser_query.set_defaults(func=query)

    parser_docker_run = subparsers.add_parser('docker-run', help='Run docker containers on remote hosts.')
    parser_docker_run.add_argument(
        "-r",
        "--stop-and-remove",
        action="store",
        metavar="CONTAINER",
        help="First, stop and remove CONTAINER before running the new container.")
    parser_docker_run.set_defaults(func=docker_run)

    parser_rpm = subparsers.add_parser('rpm', help='Manage RPM packages on remote hosts.')
    parser_rpm.add_argument(
        "package",
        action="store",
        help="RPM package name or path.")
    mxg = parser_rpm.add_mutually_exclusive_group(required=False)
    mxg.add_argument(
        "-u",
        "--uninstall",
        action="store_true",
        help="Uninstall the package.")
    mxg.add_argument(
        "-l",
        "--local",
        action="store_true",
        help="PACKAGE is a path to a local package that must first be copied to the remote host.")
    del mxg
    parser_rpm.set_defaults(func=manage_rpm)

    parser_shell = subparsers.add_parser('shell', help='Run arbitrary shell commands.')
    parser_shell.add_argument(
        "-s",
        "--sudo",
        action="store_true",
        help="Use `sudo` to execute the remote command.")
    parser_shell.add_argument(
        "arg",
        action="store",
        nargs=argparse.REMAINDER,
        help="Arguments that will be passed to the remote shell")
    parser_shell.set_defaults(func=execute_shell)

    args = parser.parse_args()
    main(args)

