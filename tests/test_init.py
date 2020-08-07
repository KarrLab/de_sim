"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-08-06
:Copyright: 2020, Karr Lab
:License: MIT
"""

import unittest

import de_sim


class TestEvent(unittest.TestCase):

    def test(self):
        self.assertTrue(hasattr(de_sim, 'SimulationMessage'))
        self.assertTrue(hasattr(de_sim, 'ApplicationSimulationObject'))
        self.assertTrue(hasattr(de_sim, 'SimulationEngine'))
        self.assertTrue(hasattr(de_sim, 'Event'))
