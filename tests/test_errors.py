"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-01-22
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

import unittest

from de_sim.errors import SimulatorError


class TestErrors(unittest.TestCase):

    def setUp(self):
        self.test_msg = 'short message'

    def make_error(self):
        raise SimulatorError(self.test_msg)

    def test_errors(self):
        with self.assertRaisesRegex(SimulatorError, self.test_msg):
            self.make_error()
