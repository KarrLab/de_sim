"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-17
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

import tempfile
import unittest
from argparse import Namespace
from capturer import CaptureOutput

from de_sim.examples.random_walk import RunRandomWalkSimulation


class TestRandomStateVariableSimulation(unittest.TestCase):

    def test_random_walk_simulation(self):
        with CaptureOutput(relay=False):
            with tempfile.NamedTemporaryFile() as file_like_obj:
                out_file = file_like_obj.name
                args = Namespace(max_time=10, plot_file=out_file, output=False)
                self.assertTrue(0 < RunRandomWalkSimulation.main(args))
                args = Namespace(max_time=10, plot_file=out_file, output=True)
                self.assertTrue(0 < RunRandomWalkSimulation.main(args))
