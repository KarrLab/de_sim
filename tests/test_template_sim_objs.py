"""
:Author: Arthur Goldberg, Arthur.Goldberg@mssm.edu
:Date: 2018-10-19
:Copyright: 2018, Karr Lab
:License: MIT
"""

import unittest
import os
import numpy as np

from de_sim.simulation_engine import SimulationEngine
from de_sim.template_sim_objs import TemplatePeriodicSimulationObject
from de_sim.errors import SimulatorError


class PeriodicSimulationObject(TemplatePeriodicSimulationObject):
    def __init__(self, name, period):
        self.times = []
        super().__init__(name, period)

    def handle_event(self):
        """Handle the periodic event"""
        self.times.append(self.time)


class TestTemplatePeriodicSimulationObject(unittest.TestCase):

    def test_TemplatePeriodicSimulationObject(self):

        simulator = SimulationEngine()
        end_time = 5
        expected = []

        # int period
        period = 1
        pso_1 = PeriodicSimulationObject('pso_1', period)
        expected.append(np.linspace(0, end_time, end_time + 1))

        # float period
        period = .1
        pso_2 = PeriodicSimulationObject('pso_2', period)
        expected.append(np.linspace(0, end_time, end_time * 10 +1))

        psos = [pso_1, pso_2]
        simulator.add_objects(psos)
        simulator.initialize()
        simulator.simulate(end_time)

        for pso, expect in zip(psos, expected):
            self.assertEqual(pso.times, list(expect))

    def test_exceptions(self):
        with self.assertRaisesRegexp(SimulatorError, 'period must be positive'):
            PeriodicSimulationObject('pso', -1)
