""" Generate a space-time plot of PHOLD

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-06-22
:Copyright: 2020, Karr Lab
:License: MIT
"""

from argparse import Namespace
import os
import re

from de_sim.examples.phold import RunPhold
from de_sim.visualize import SpaceTime


# TODO(Arthur): all docstrings, make config changes work consistently
# TODO(Arthur): unittest; make context manager that removes temp file; move to wc_utils
# utility for changing config values when testing
SOURCE_CONFIG_FILENAME = os.path.join(os.path.dirname(__file__), '..', '..', 'wc_sim', 'config', 'core.default.cfg')
TEMP_CONFIG_FILENAME = os.path.expanduser(os.path.join('~', '.wc', 'wc_sim.core.cfg'))


class ConfigFileModifier(object):
    """ Modify the core config file to easily enable testing

    To use, load the config information at run-time, not compile-time.

    Attributes:
        source_config_filename (:obj:`str`): filename of the permanent config file
        temp_config_filename (:obj:`str`): filename of a temporary config file on the path that loads config files
    """

    def __init__(self, source_config_filename=SOURCE_CONFIG_FILENAME, temp_config_filename=TEMP_CONFIG_FILENAME):
        self.source_config_filename = source_config_filename
        self.temp_config_filename = temp_config_filename

    def write_test_config_file(self, replacements):
        """ Write a modified config file for testing

        Args:
            replacements (:obj:`list` of :obj:`tuple`): iterator over pairs of 'attribute', 'replacement value';
                each config attribute in `self.source_config_filename` is replaced with its replacement value
        """
        with open(self.source_config_filename, 'r') as f:
            source_config = f.read()
        modified_config = source_config
        for name, value in replacements:
            modified_config = re.sub(f"{name} .*", f"{name} = {value}", modified_config)
        with open(self.temp_config_filename, 'w') as f:
            f.write(modified_config)

    def clean_up(self):
        """ Remove the temporary config file
        """
        try:
            os.remove(self.temp_config_filename)
        except FileNotFoundError:
            pass


def run_phold(time_max, frac_self_events=0.5, num_phold_procs=3, seed=17):
    args = Namespace(time_max=time_max, frac_self_events=frac_self_events,
                     num_phold_procs=num_phold_procs, seed=seed)
    RunPhold.main(args)


def prepare_plot():
    # turn on plot logging through config
    source_config_filename = os.path.join(os.path.dirname(__file__), '..', 'de_sim', 'config', 'core.default.cfg')
    temp_config_filename = os.path.expanduser('~/.wc/de_sim.core.cfg')
    config_file_modifier = ConfigFileModifier(source_config_filename=source_config_filename,
                                              temp_config_filename=temp_config_filename)
    config_file_modifier.write_test_config_file([('log_events', 'True')])

    source_debug_conf_filename = os.path.join(os.path.dirname(__file__), '..', 'de_sim', 'config',
                                              'debug.default.cfg')
    temp_debug_conf_filename = os.path.expanduser('~/.wc/de_sim.debug.cfg')
    debug_conf_file_modifier = ConfigFileModifier(source_config_filename=source_debug_conf_filename,
                                                  temp_config_filename=temp_debug_conf_filename)
    debug_conf_file_modifier.write_test_config_file([('level', 'debug')])

    plot_log = os.path.expanduser('~/.wc/log/de_sim.plot.log')
    try:
        os.remove(plot_log)
    except FileNotFoundError:
        pass
    run_phold(8)
    space_time = SpaceTime()
    space_time.get_data(plot_log)
    space_time_plot = os.path.join(os.path.dirname(__file__), "phold_space_time_plot.png")
    space_time.plot_data(space_time_plot)

    config_file_modifier.clean_up()
    debug_conf_file_modifier.clean_up()


prepare_plot()
