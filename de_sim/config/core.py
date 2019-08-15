""" wc_sim core configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-09-19
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import configobj
import os
import pkg_resources
import wc_utils.config.core
import wc_utils.debug_logs.config


def get_config(extra=None):
    """ Get configuration

    Args:
        extra (:obj:`dict`, optional): additional configuration to override

    Returns:
        :obj:`configobj.ConfigObj`: nested dictionary with the configuration settings loaded from the configuration source(s).
    """
    paths = wc_utils.config.core.ConfigPaths(
        default=pkg_resources.resource_filename('wc_sim', 'core/config/core.default.cfg'),
        schema=pkg_resources.resource_filename('wc_sim', 'core/config/core.schema.cfg'),
        user=(
            'wc_sim.core.core.cfg',
            os.path.expanduser('~/.wc/wc_sim.core.core.cfg'),
        ),
    )
    return wc_utils.config.core.ConfigManager(paths).get_config(extra=extra)


def get_debug_logs_config(extra=None):
    """ Get debug logs configuration

    Args:
        extra (:obj:`dict`, optional): additional configuration to override

    Returns:
        :obj:`configobj.ConfigObj`: nested dictionary with the configuration settings loaded from the configuration source(s).
    """
    paths = wc_utils.debug_logs.config.paths.deepcopy()
    paths.default = pkg_resources.resource_filename('wc_sim', 'core/config/debug.default.cfg')
    paths.user = (
        'wc_sim.core.debug.cfg',
        os.path.expanduser('~/.wc/wc_sim.core.debug.cfg'),
    )
    return wc_utils.config.core.ConfigManager(paths).get_config(extra=extra)
