
from deployer import config
from deployer.config_deployer import (
    deploy_config
)
from deployer.package_deployer import (
    install_package,
    install_local_package,
    remove_package,
)
from deployer.superuser import root_cmd

config.load_config()

