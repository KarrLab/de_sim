"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-17
:Copyright: 2018, Karr Lab
:License: MIT
"""

import unittest
import warnings
from pprint import pprint
from argparse import Namespace

from examples.minimal_simulation import RunMinimalSimulation
from de_sim.config import core


class TestMinimalSimulation(unittest.TestCase):

    def setUp(self):
        self.config = core.get_debug_logs_config()
        # turn off console logging
        self.console_level = self.config['debug_logs']['handlers']['debug.console']['level']
        self.config['debug_logs']['handlers']['debug.console']['level'] = 'error'
        warnings.simplefilter("ignore")

    def tearDown(self):
        # restore console logging
        self.config['debug_logs']['handlers']['debug.console']['level'] = self.console_level

    def run_minimal_simulation(self, delay, end_time):
        args = Namespace(delay=delay, end_time=end_time)
        return(RunMinimalSimulation.main(args))

    def test_minimal_simulation_reproducibility(self):
        num_events1=self.run_minimal_simulation(2, 20)
        num_events2=self.run_minimal_simulation(2, 20)
        self.assertEqual(num_events1, num_events2)

    def test_minimal_simulation_parse_args(self):
        delay = 3
        end_time = 25.0
        cl = "{} {}".format(delay, end_time)
        args = RunMinimalSimulation.parse_args(cli_args=cl.split())
        self.assertEqual(args.delay, delay)
        self.assertEqual(args.end_time, end_time)
