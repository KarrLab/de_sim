""" Simulation configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-03-16
:Copyright: 2020, Karr Lab
:License: MIT
"""

from dataclasses import dataclass
import unittest
import shutil
import tempfile

from de_sim.errors import SimulatorError
from de_sim.simulation_config import validate_dataclass_types, SimulationConfig

class TestSimulationConfig(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.time_max = 10.0
        self.time_init = 3.5

        class ExampleClass(object):
            def f(): pass
        ec = ExampleClass()
        self.stop_condition = ec.f

        self.progress = True
        self.metadata_dir = self.tmp_dir
        self.simulation_config = SimulationConfig(self.time_max, self.time_init,
                                                  self.stop_condition, self.progress, self.metadata_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test(self):
        self.assertEquals(self.simulation_config.time_max, self.time_max)
        self.assertEquals(self.simulation_config.time_init, self.time_init)
        self.assertEquals(self.simulation_config.stop_condition, self.stop_condition)
        self.assertEquals(self.simulation_config.progress, self.progress)
        self.assertEquals(self.simulation_config.metadata_dir, self.metadata_dir)

        # check defaults
        simulation_config = SimulationConfig(self.time_max)
        self.assertEquals(simulation_config.time_init, 0.0)
        self.assertEquals(simulation_config.stop_condition, None)
        self.assertEquals(simulation_config.progress, False)
        self.assertEquals(simulation_config.metadata_dir, None)

        # check keywords
        simulation_config = SimulationConfig(time_max=self.time_max)
        self.assertEquals(simulation_config.time_max, self.time_max)

    def test_validate_individual_fields(self):

        # accept ints in float fields
        simulation_config = SimulationConfig(int(self.time_max))
        self.assertEquals(simulation_config.time_max, self.time_max)

        time_max = 'no'
        with self.assertRaisesRegex(SimulatorError, 'time_max .* must be a float'):
            SimulationConfig(time_max)

        with self.assertRaisesRegex(SimulatorError, 'time_init .* must be a float'):
            SimulationConfig(self.time_max, time_init=set())

        with self.assertRaisesRegex(SimulatorError, "stop_condition .* must be a function"):
            SimulationConfig(self.time_max, stop_condition='hi')

        with self.assertRaisesRegex(SimulatorError, "metadata_dir .* must be a directory"):
            SimulationConfig(self.time_max, metadata_dir='not a dir')

        # test 'an int'
        @dataclass
        class TestClass:
            i: int
        tc = TestClass(1.3)
        with self.assertRaisesRegex(Exception, "an int"):
            validate_dataclass_types(tc, Exception)

    def test_validate(self):
        try:
            self.simulation_config.validate()
        except SimulatorError:
            self.fail("self.simulation_config.validate() shouldn't raise SimulatorError")

        # validate with defaults
        simulation_config = SimulationConfig(self.time_max)
        try:
            simulation_config.validate()
        except SimulatorError:
            self.fail("simulation_config.validate() shouldn't raise SimulatorError")

        self.simulation_config.time_max = self.time_init - 1
        with self.assertRaisesRegex(SimulatorError, 'time_max .* must be greater than time_init .*'):
            self.simulation_config.validate()
