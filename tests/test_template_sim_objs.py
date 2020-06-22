"""
:Author: Arthur Goldberg, Arthur.Goldberg@mssm.edu
:Date: 2018-10-19
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

import unittest
import os
import math
import numpy as np

from de_sim.errors import SimulatorError
from de_sim.simulation_config import SimulationConfig
from de_sim.simulation_engine import SimulationEngine
from de_sim.template_sim_objs import TemplatePeriodicSimulationObject


class SpecialPeriodicSimulationObject(TemplatePeriodicSimulationObject):
    def __init__(self, name, period, start_time=0.):
        self.times = []
        super().__init__(name, period, start_time=start_time)

    def handle_event(self):
        """Handle the periodic event"""
        self.times.append(self.time)


class TestTemplatePeriodicSimulationObject(unittest.TestCase):

    def test_TemplatePeriodicSimulationObject(self):

        simulator = SimulationEngine()
        time_max = 5
        expected = []

        # int period
        period = 1
        pso_1 = SpecialPeriodicSimulationObject('pso_1', period)
        expected.append(np.linspace(0, time_max, time_max + 1))

        period = .1
        pso_2 = SpecialPeriodicSimulationObject('pso_2', period)
        expected.append([t/10 for t in range(time_max * 10 + 1)])

        psos = [pso_1, pso_2]
        simulator.add_objects(psos)
        simulator.initialize()
        simulator.simulate(time_max)

        for pso, expect in zip(psos, expected):
            for pso_time, expect_time in zip(pso.times, expect):
                self.assertTrue(math.isclose(pso_time, expect_time))

    def test_exceptions(self):
        with self.assertRaisesRegexp(SimulatorError, 'period must be positive'):
            SpecialPeriodicSimulationObject('pso', -1)

    def test_non_zero_time_init(self):

        for time_init in [-3, 2]:
            simulator = SimulationEngine()
            time_max = 5
            period = 1
            pso = SpecialPeriodicSimulationObject('pso', period, time_init)
            expected_times = list(np.linspace(time_init, time_max, time_max - time_init + 1))
            simulator.add_objects([pso])
            simulator.initialize()
            simulation_config = SimulationConfig(time_max, time_init)
            simulator.simulate(sim_config=simulation_config)
            self.assertEqual(expected_times, pso.times)
