""" Generate a space-time plot of PHOLD

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-06-22
:Copyright: 2020, Karr Lab
:License: MIT
"""

from argparse import Namespace
import os
import tempfile

from de_sim.examples.phold import RunPhold
from de_sim.testing.utilities_for_testing import unset_env_var
from de_sim.visualize import SpaceTime
from wc_utils.util.environ import EnvironUtils
import de_sim


def run_phold(max_time, num_phold_procs=3, frac_self_events=0.5):
    """ Run PHOLD, and generate a plot log

    Args:
        extra (:obj:`float`): simulation duration
        num_phold_procs (:obj:`int`, optional): number of PHOLD processes to run
        frac_self_events (:obj:`float`, optional): fraction of events sent to self
    """
    args = Namespace(max_time=max_time, num_phold_procs=num_phold_procs,
                     frac_self_events=frac_self_events)
    RunPhold.main(args)


def create_phold_space_time_diagram():
    """ Run PHOLD, and use plot log to generate a space-time diagram """
    plot_log = os.path.expanduser('~/.wc/log/de_sim.plot.log')
    try:
        os.remove(plot_log)
    except FileNotFoundError:
        pass
    run_phold(8)
    space_time = SpaceTime()
    space_time.get_data(plot_log)
    temp_dir = tempfile.TemporaryDirectory()
    space_time_plot = os.path.join(temp_dir.name, "phold_space_time_plot.pdf")
    with unset_env_var('DISPLAY'):
        space_time.plot_data(space_time_plot)
    print('space-time diagram written to', space_time_plot)


with EnvironUtils.temp_config_env(((['de_sim', 'log_events'], 'True'),
                                   (['debug_logs', 'handlers', 'plot.file', 'level'], 'debug'))):
    create_phold_space_time_diagram()
