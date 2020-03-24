""" Simulation configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-03-16
:Copyright: 2020, Karr Lab
:License: MIT
"""

from dataclasses import dataclass
import os
import unittest
import shutil
import tempfile

from de_sim.errors import SimulatorError
from de_sim.simulation_config import SimulationConfig, ValidatedDataClass


class TestValidatedDataClass(unittest.TestCase):

        @dataclass
        class TestClass(ValidatedDataClass):
            i: int
            f: float = 0.0
            s: str = None

        def test_validate_dataclass_type(self):

            tc = self.TestClass(1, 2.2)
            self.assertEquals(tc.validate_dataclass_type('i'), None)
            self.assertEquals(tc.validate_dataclass_type('f'), None)
            tc_2 = self.TestClass(1, 2)
            self.assertEquals(tc.validate_dataclass_type('f'), None)

            # test 'an' int, no default
            with self.assertRaisesRegex(TypeError, "an int"):
                self.TestClass(1.3)

            # test default
            with self.assertRaisesRegex(TypeError, "a float"):
                self.TestClass(2, 'h')

            # test bad name
            tc_3 = self.TestClass(2)
            with self.assertRaises(ValueError):
                tc_3.validate_dataclass_type('bad name')

        def test_validate_dataclass_types(self):

            tc = self.TestClass(1, 2.2)
            self.assertEquals(tc.validate_dataclass_types(), None)


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
        self.data_dir = self.tmp_dir
        self.simulation_config = SimulationConfig(self.time_max, self.time_init,
                                                  self.stop_condition, self.progress, self.data_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test(self):
        self.assertEquals(self.simulation_config.time_max, self.time_max)
        self.assertEquals(self.simulation_config.time_init, self.time_init)
        self.assertEquals(self.simulation_config.stop_condition, self.stop_condition)
        self.assertEquals(self.simulation_config.progress, self.progress)
        self.assertEquals(self.simulation_config.data_dir, self.data_dir)

        # check defaults
        simulation_config = SimulationConfig(self.time_max)
        self.assertEquals(simulation_config.time_init, 0.0)
        self.assertEquals(simulation_config.stop_condition, None)
        self.assertEquals(simulation_config.progress, False)
        self.assertEquals(simulation_config.data_dir, None)

        # check keywords
        simulation_config = SimulationConfig(time_max=self.time_max)
        self.assertEquals(simulation_config.time_max, self.time_max)

    def test_setattr(self):

        # accept ints in float fields
        simulation_config = SimulationConfig(int(self.time_max))
        self.assertEquals(simulation_config.time_max, self.time_max)

        time_max = 'no'
        with self.assertRaisesRegex(SimulatorError, 'time_max .* must be a float'):
            SimulationConfig(time_max)

        with self.assertRaisesRegex(SimulatorError, 'time_init .* must be a float'):
            SimulationConfig(self.time_max, time_init=set())

    def test_validate_individual_fields(self):

        with self.assertRaisesRegex(SimulatorError, "stop_condition .* must be a function"):
            cfg = SimulationConfig(self.time_max, stop_condition='hi')
            cfg.validate_individual_fields()

        # test data_dir
        # test data_dir specified relative to home directory
        usr_tmp = os.path.join('~', 'tmp')
        usr_tmp_abs = os.path.expanduser(usr_tmp)
        data_dir = os.path.join(usr_tmp, 'data_dir')
        cfg = SimulationConfig(self.time_max, data_dir=data_dir)
        self.assertEquals(cfg.validate_individual_fields(), None)
        self.assertTrue(os.path.isdir(cfg.data_dir))

        _, tmp_file = tempfile.mkstemp(dir=self.tmp_dir)
        with self.assertRaisesRegex(SimulatorError, "data_dir .* must be a directory"):
            cfg = SimulationConfig(self.time_max, data_dir=tmp_file)
            cfg.validate_individual_fields()

        with self.assertRaisesRegex(SimulatorError, "data_dir .* is not empty"):
            cfg = SimulationConfig(self.time_max, data_dir=self.tmp_dir)
            cfg.validate_individual_fields()

        # data_dir gets created because it does not exist
        data_dir = os.path.join(self.tmp_dir, 'no_such_dir', 'no_such_sub_dir')
        cfg = SimulationConfig(self.time_max, data_dir=data_dir)
        cfg.validate_individual_fields()
        self.assertTrue(os.path.isdir(cfg.data_dir))

        # data_dir already exists
        tmp_dir = tempfile.mkdtemp(dir=self.tmp_dir)
        cfg = SimulationConfig(self.time_max, data_dir=tmp_dir)
        self.assertEquals(cfg.validate_individual_fields(), None)

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
