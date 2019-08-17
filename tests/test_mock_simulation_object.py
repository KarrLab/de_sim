"""

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-06
:Copyright: 2018, Karr Lab
:License: MIT
"""
import unittest

from de_sim.testing.mock_simulation_object import MockSimulationObject
from de_sim.testing.some_message_types import Eg1


class Example(MockSimulationObject):

    def send_initial_events(self): pass

    def get_state(self):
        return 'object state to be provided'

    def test_handler(self, value):
        self.test_case.assertEqual(value, self.kwargs['expected'])

    event_handlers = [(Eg1, test_handler)]


class TestMockSimulationObject(unittest.TestCase):

    def test(self):
        t = Example('name', self, a=1, expected=2)
        t.test_handler(2)

        with self.assertRaises(ValueError) as context:
            Example('name', 'string')
        self.assertIn("'test_case' should be a unittest.TestCase instance", str(context.exception))