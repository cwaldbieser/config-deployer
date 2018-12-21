#! /usr/bin/env python

import argparse
import sys
from deployer.config import load_config
from deployer import config_deployer

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

    args = parser.parse_args()
    main(args)

