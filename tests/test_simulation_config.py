""" Simulation configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-03-16
:Copyright: 2020, Karr Lab
:License: MIT
"""

import copy
import os
import pickle
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

        class ExampleClass(object):
            def f(): pass
        ec = ExampleClass()
        self.stop_condition = ec.f

        self.progress = True
        self.output_dir = self.tmp_dir
        self.simulation_config = SimulationConfig(self.time_max, self.time_init,
                                                  self.stop_condition, self.output_dir, self.progress)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test(self):
        self.assertEquals(self.simulation_config.time_max, self.time_max)
        self.assertEquals(self.simulation_config.time_init, self.time_init)
        self.assertEquals(self.simulation_config.stop_condition, self.stop_condition)
        self.assertEquals(self.simulation_config.progress, self.progress)
        self.assertEquals(self.simulation_config.output_dir, self.output_dir)

        # check defaults
        simulation_config = SimulationConfig(self.time_max)
        self.assertEquals(simulation_config.time_init, 0.0)
        self.assertEquals(simulation_config.stop_condition, None)
        self.assertEquals(simulation_config.progress, False)
        self.assertEquals(simulation_config.output_dir, None)

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

        # test output_dir
        # test output_dir specified relative to home directory
        usr_tmp = os.path.join('~', 'tmp')
        usr_tmp_abs = os.path.expanduser(usr_tmp)
        output_dir = os.path.join(usr_tmp, 'output_dir')
        cfg = SimulationConfig(self.time_max, output_dir=output_dir)
        self.assertEquals(cfg.validate_individual_fields(), None)
        self.assertTrue(os.path.isdir(cfg.output_dir))

        _, tmp_file = tempfile.mkstemp(dir=self.tmp_dir)
        with self.assertRaisesRegex(SimulatorError, "output_dir .* must be a directory"):
            cfg = SimulationConfig(self.time_max, output_dir=tmp_file)
            cfg.validate_individual_fields()

        with self.assertRaisesRegex(SimulatorError, "output_dir .* is not empty"):
            cfg = SimulationConfig(self.time_max, output_dir=self.tmp_dir)
            cfg.validate_individual_fields()

        # output_dir gets created because it does not exist
        output_dir = os.path.join(self.tmp_dir, 'no_such_dir', 'no_such_sub_dir')
        cfg = SimulationConfig(self.time_max, output_dir=output_dir)
        cfg.validate_individual_fields()
        self.assertTrue(os.path.isdir(cfg.output_dir))

        # output_dir already exists
        tmp_dir = tempfile.mkdtemp(dir=self.tmp_dir)
        cfg = SimulationConfig(self.time_max, output_dir=tmp_dir)
        self.assertEquals(cfg.validate_individual_fields(), None)

        with self.assertRaisesRegex(SimulatorError, "object_memory_change_interval .* must be non-negative"):
            cfg = SimulationConfig(self.time_max, object_memory_change_interval=-3)
            cfg.validate_individual_fields()

    def test_all_fields(self):
        profile = True
        kwargs = dict(time_max=self.time_max,
                      time_init=self.time_init,
                      stop_condition=self.stop_condition,
                      output_dir=self.output_dir,
                      progress=self.progress,
                      profile=profile)
        simulation_config = SimulationConfig(self.time_max, self.time_init, self.stop_condition,
                                             self.output_dir, self.progress, profile)
        simulation_config.validate()
        for attr, value in kwargs.items():
            self.assertEquals(getattr(simulation_config, attr), value)

        simulation_config = SimulationConfig(**kwargs)
        simulation_config.validate()
        for attr, value in kwargs.items():
            self.assertEquals(getattr(simulation_config, attr), value)

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

        self.simulation_config.time_max = 10
        self.simulation_config.profile = True
        self.simulation_config.object_memory_change_interval = 100
        with self.assertRaisesRegex(SimulatorError, 'profile and object_memory_change_interval cannot both be active'):
            self.simulation_config.validate()

    simulation_config_no_stop_cond = SimulationConfig(10.0, 3.5, output_dir=tempfile.mkdtemp(), progress=True)

    def test_deepcopy(self):
        simulation_config_copy = copy.deepcopy(self.simulation_config_no_stop_cond)
        self.assertEquals(self.simulation_config_no_stop_cond, simulation_config_copy)

    def test_semantically_equal(self):
        simulation_config = SimulationConfig(self.time_max, self.time_init,
                                             self.stop_condition, self.output_dir, self.progress)
        self.assertTrue(self.simulation_config.semantically_equal(simulation_config))
        simulation_config.progress = not simulation_config.progress
        # progress is not semantically meaningful
        self.assertTrue(self.simulation_config.semantically_equal(simulation_config))
        simulation_config.time_max += 1E-12
        self.assertFalse(self.simulation_config.semantically_equal(simulation_config))


class ExampleClass(object):
    def f(): pass
ec = ExampleClass()


class TestPickleSimulationConfig(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    simulation_config = SimulationConfig(10.0, 3.5, stop_condition=ec.f, output_dir=tempfile.mkdtemp(), progress=True)

    def test_prepare_to_pickle(self):
        self.simulation_config.validate()
        file = os.path.join(self.tmp_dir, 'test2.pickle')
        prepared_to_pickle = self.simulation_config.prepare_to_pickle()
        with open(file, 'wb') as fd:
            pickle.dump(prepared_to_pickle, fd)
        with open(file, 'rb') as fd:
            simulation_config = pickle.load(fd)
        self.assertEquals(prepared_to_pickle, simulation_config)
        shutil.rmtree(self.simulation_config.output_dir)
