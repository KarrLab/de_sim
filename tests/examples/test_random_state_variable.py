"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-17
:Copyright: 2018, Karr Lab
:License: MIT
"""

import unittest
import warnings
from capturer import CaptureOutput
from argparse import Namespace

from examples.random_state_variable import RunRandomStateVariableSimulation
from de_sim.config import core


class TestRandomStateVariableSimulation(unittest.TestCase):

    def setUp(self):
        # turn off console logging
        self.config = core.get_debug_logs_config()
        self.console_level = self.config['debug_logs']['handlers']['debug.console']['level']
        self.config['debug_logs']['handlers']['debug.console']['level'] = 'error'
        warnings.simplefilter("ignore")

    def tearDown(self):
        # restore console logging
        self.config['debug_logs']['handlers']['debug.console']['level'] = self.console_level

    def test_random_state_variable_simulation(self):
        with CaptureOutput(relay=False):
            args = Namespace(initial_state=3, end_time=10, output=False)
            self.assertTrue(0<RunRandomStateVariableSimulation.main(args))
            args = Namespace(initial_state=3, end_time=10, output=True)
            self.assertTrue(0<RunRandomStateVariableSimulation.main(args))
