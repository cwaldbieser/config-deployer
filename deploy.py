#! /usr/bin/env python

import argparse
import sys
from deployer.config import load_config
from deployer import config_deployer
from deployer import docker
from deployer import introspect
from deployer import package_deployer

def deploy_config(args):
    """
    Deploy a configuration.
    """
    cfg = load_config(args.config, args.stage)
    pool = cfg.conn_pool
    for conn in pool:
        config_deployer.deploy_config(
            conn,
            cfg,
            src_commit=args.commit,
            move_etc=(not args.no_etc) and (args.archive is None),
            local_archive=args.archive)

def query(args):
    """
    Interrogate runtime configuration.
    """
    cfg = load_config(args.config, args.stage)
    introspect.list_hosts(cfg)

def docker_run(args):
    """
    Run a docker container on remote hosts.
    """
    cfg = load_config(args.config, args.stage)
    pool = cfg.conn_pool
    for conn in pool:
        docker.docker_run(conn, cfg, args.stop_and_remove)

def manage_rpm(args):
    """
    Manage RPM packages on remote hosts.
    """
    cfg = load_config(args.config, args.stage)
    pool = cfg.conn_pool
    for conn in pool:
        if args.local:
            package_deployer.install_local_rpm(conn, args.package)
        elif args.uninstall:
            package_deployer.remove_rpm(conn, args.package)
        else:
            package_deployer.install_rpm(conn, args.package)

def main(args):
    """
    Main function.
    """
    if not 'func' in args:
        print("Invalid command.", file=sys.stderr)
        sys.exit(1)
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

    args = parser.parse_args()
    main(args)

