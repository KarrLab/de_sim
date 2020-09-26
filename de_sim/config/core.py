""" de_sim core configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-09-19
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

import configobj  # noqa: F401
import os
import pkg_resources

from wc_utils.debug_logs.core import DebugLogsManager
import wc_utils.config.core
import wc_utils.debug_logs.config


def get_config(extra=None):
    """ Get configuration

    Args:
        extra (:obj:`dict`, optional): additional configuration to override

    Returns:
        :obj:`configobj.ConfigObj`: nested dictionary with the configuration settings loaded from the
        configuration source(s).
    """
    paths = wc_utils.config.core.ConfigPaths(
        default=pkg_resources.resource_filename('de_sim', 'config/core.default.cfg'),
        schema=pkg_resources.resource_filename('de_sim', 'config/core.schema.cfg'),
        user=(
            'de_sim.core.cfg',
            os.path.expanduser('~/.wc/de_sim.core.cfg'),
        ),
    )
    return wc_utils.config.core.ConfigManager(paths).get_config(extra=extra)


def get_debug_logs_config(extra=None, cfg_path=('de_sim', 'config/debug.default.cfg')):
    """ Get debug logs configuration

    Args:
        extra (:obj:`dict`, optional): additional configuration to override
        cfg_path (:obj:`str`, optional): path to the debug logs config file

    Returns:
        :obj:`configobj.ConfigObj`: nested dictionary with the configuration settings loaded from the
        configuration source(s).
    """
    paths = wc_utils.debug_logs.config.paths.deepcopy()
    paths.default = pkg_resources.resource_filename(*cfg_path)
    paths.user = (
        'de_sim.debug.cfg',
        os.path.expanduser('~/.wc/de_sim.debug.cfg'),
    )
    return wc_utils.config.core.ConfigManager(paths).get_config(extra=extra)


def get_debug_logs(extra=None):
    """ Get debug logs

    Args:
        extra (:obj:`dict`, optional): additional configuration to override

    Returns:
        :obj:`wc_utils.debug_logs.core.DebugLogsManager`: a `DebugLogsManager`
    """
    config = get_debug_logs_config(extra)
    return DebugLogsManager().setup_logs(config)
