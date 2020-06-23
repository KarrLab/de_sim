"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-17
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

import unittest
import warnings
from pprint import pprint
from argparse import Namespace

from de_sim.examples.minimal_simulation import RunMinimalSimulation
from de_sim.config import core


class TestMinimalSimulation(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("ignore")

    def run_minimal_simulation(self, delay, time_max):
        args = Namespace(delay=delay, time_max=time_max)
        return(RunMinimalSimulation.main(args))

    def test_minimal_simulation_reproducibility(self):
        num_events1=self.run_minimal_simulation(2, 20)
        num_events2=self.run_minimal_simulation(2, 20)
        self.assertEqual(num_events1, num_events2)

    def test_minimal_simulation_parse_args(self):
        delay = 3
        time_max = 25.0
        cl = "{} {}".format(delay, time_max)
        args = RunMinimalSimulation.parse_args(cli_args=cl.split())
        self.assertEqual(args.delay, delay)
        self.assertEqual(args.time_max, time_max)
