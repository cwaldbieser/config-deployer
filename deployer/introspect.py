

def list_hosts(cfg):
    """
    List all the hosts for the current stage.
    """
    print("== Hosts for stage `{}` ==".format(cfg.stage))
    for host in cfg.settings['roles'][cfg.stage]['target-hosts']:
        print(host)

