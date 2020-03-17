""" Simulation configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-03-16
:Copyright: 2020, Karr Lab
:License: MIT
"""

import unittest
import shutil
import tempfile

from de_sim.errors import SimulatorError
from de_sim.simulation_config import SimulationConfig


class TestSimulationConfig(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.time_max = 10.0
        self.time_init = 3.5
        self.random_seed = 7
        def f(): pass
        self.stop_condition = f
        self.progress = True
        self.metadata_dir = self.tmp_dir
        self.simulation_config = SimulationConfig(self.time_max, self.time_init, self.random_seed,
                                                  self.stop_condition, self.progress, self.metadata_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test(self):
        self.assertEquals(self.simulation_config.time_max, self.time_max)
        self.assertEquals(self.simulation_config.time_init, self.time_init)
        self.assertEquals(self.simulation_config.random_seed, self.random_seed)
        self.assertEquals(self.simulation_config.stop_condition, self.stop_condition)
        self.assertEquals(self.simulation_config.progress, self.progress)
        self.assertEquals(self.simulation_config.metadata_dir, self.metadata_dir)

        # check defaults
        simulation_config = SimulationConfig(self.time_max)
        self.assertEquals(simulation_config.time_init, 0.0)
        self.assertEquals(simulation_config.random_seed, None)
        self.assertEquals(simulation_config.stop_condition, None)
        self.assertEquals(simulation_config.progress, False)
        self.assertEquals(simulation_config.metadata_dir, None)

        # check keywords
        simulation_config = SimulationConfig(_time_max=self.time_max)
        self.assertEquals(simulation_config.time_max, self.time_max)

    def test_validate(self):
        try:
            self.simulation_config.validate()
        except SimulatorError:
            self.fail("simulation_config.validate() shouldn't raise SimulatorError")

        # validate with defaults
        simulation_config = SimulationConfig(self.time_max)
        try:
            simulation_config.validate()
        except SimulatorError:
            self.fail("simulation_config.validate() shouldn't raise SimulatorError")

        time_max = 'no'
        simulation_config = SimulationConfig(time_max)
        with self.assertRaisesRegex(SimulatorError, 'time_max .* is not a\(n\) float'):
            simulation_config.validate()

        simulation_config = SimulationConfig(self.time_max, _time_init=set())
        with self.assertRaisesRegex(SimulatorError, 'time_init .* is not a\(n\) float'):
            simulation_config.validate()

        simulation_config = SimulationConfig(self.time_max, self.time_max + 1)
        with self.assertRaisesRegex(SimulatorError, 'time_max .* must be greater than time_init .*'):
            simulation_config.validate()

        simulation_config = SimulationConfig(self.time_max, _stop_condition='hi')
        with self.assertRaisesRegex(SimulatorError, "stop_condition .* is not a function"):
            simulation_config.validate()

        simulation_config = SimulationConfig(self.time_max, _metadata_dir='not a dir')
        with self.assertRaisesRegex(SimulatorError, "metadata_dir .* is not a directory"):
            simulation_config.validate()

    def test_properties(self):
        # test all setters and getters
        new_time_max = self.time_max + 0.1
        self.simulation_config.time_max = new_time_max
        self.assertEquals(self.simulation_config.time_max, new_time_max)

        new_time_init = self.time_init + 0.1
        self.simulation_config.time_init = new_time_init
        self.assertEquals(self.simulation_config.time_init, new_time_init)

        new_random_seed = self.random_seed + 1
        self.simulation_config.random_seed = new_random_seed
        self.assertEquals(self.simulation_config.random_seed, new_random_seed)

        def g(): pass
        new_stop_condition = g
        self.simulation_config.stop_condition = new_stop_condition
        self.assertEquals(self.simulation_config.stop_condition, new_stop_condition)

        new_progress = not self.progress
        self.simulation_config.progress = new_progress
        self.assertEquals(self.simulation_config.progress, new_progress)

        new_metadata_dir = tempfile.mkdtemp(dir=self.tmp_dir)
        self.simulation_config.metadata_dir = new_metadata_dir
        self.assertEquals(self.simulation_config.metadata_dir, new_metadata_dir)

        # test validation in setter
        with self.assertRaisesRegex(SimulatorError, 'time_max .* must be greater than time_init .*'):
            self.simulation_config.time_max = self.time_init - 1
