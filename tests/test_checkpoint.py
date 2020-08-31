""" Checkpointing log tests

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-30
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

from collections import namedtuple
from numpy import random
import numpy
import os
import shutil
import tempfile
import unittest
import copy

from de_sim.checkpoint import Checkpoint, AccessCheckpoints
from de_sim.config import core
from de_sim.errors import SimulatorError
from wc_utils.util.uniform_seq import UniformSequence
import wc_utils.util.types

MAX_TIME_PRECISION = core.get_config()['de_sim']['max_time_precision']


class TestCheckpoint(unittest.TestCase):

    def setUp(self):
        self.empty_checkpoint1 = Checkpoint(None, None, None)
        self.empty_checkpoint2 = Checkpoint(None, None, None)

        # Checkpoint(time, state, random_state)
        time = 2
        state = [[1, 2], 3]
        random_state = random.RandomState(seed=0)
        attrs = dict(time=time, state=state, random_state=random_state)
        self.non_empty_checkpoint1 = Checkpoint(time, state, random_state)
        self.non_empty_checkpoint2 = self.non_empty_checkpoint1

        # make Checkpoints that differ
        diff_time = 3
        diff_state = [[1, 2], 3, 4]
        diff_random_state = random.RandomState(seed=1)
        diff_attrs = dict(time=diff_time, state=diff_state,
                          random_state=diff_random_state)
        self.diff_checkpoints = []
        for attr in ['time', 'state', 'random_state']:
            args = copy.deepcopy(attrs)
            args[attr] = copy.deepcopy(diff_attrs[attr])
            self.diff_checkpoints.append(Checkpoint(**args))

    def test_equality(self):
        obj = object()
        self.assertEqual(self.empty_checkpoint1, self.empty_checkpoint1)
        self.assertEqual(self.empty_checkpoint1, self.empty_checkpoint2)
        self.assertNotEqual(self.empty_checkpoint1, obj)
        self.assertTrue(self.empty_checkpoint1 is not None)

        self.assertEqual(self.non_empty_checkpoint1, self.non_empty_checkpoint1)
        self.assertEqual(self.non_empty_checkpoint1, self.non_empty_checkpoint2)
        self.assertNotEqual(self.non_empty_checkpoint1, obj)
        for ckpt in self.diff_checkpoints:
            self.assertNotEqual(self.non_empty_checkpoint1, ckpt)


FullSimulationState = namedtuple('FullSimulationState', 'time local_state')


class TestAccessCheckpoints(unittest.TestCase):

    def test_get_file_name(self):
        access_checkpoints = AccessCheckpoints('.')
        self.assertIn(f'{3.0:.{MAX_TIME_PRECISION}f}', access_checkpoints.get_filename(3))
        for time in [1.00000001, 1E-7]:
            with self.assertRaises(SimulatorError):
                access_checkpoints.get_filename(time)


class TestAccessCheckpointsLog(unittest.TestCase):

    def setUp(self):
        self.checkpoint_dir = tempfile.mkdtemp()
        self.out_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.checkpoint_dir)
        shutil.rmtree(self.out_dir)

    def test_constructor_creates_checkpoint_dir(self):
        checkpoint_dir = os.path.join(self.checkpoint_dir, 'checkpoint')
        checkpoint_step = 2
        init_time = 0
        MockAccessCheckpointsLogger(checkpoint_dir, checkpoint_step, init_time)
        self.assertTrue(os.path.isdir(checkpoint_dir))

    def test_mock_simulator(self):
        checkpoint_step = 2

        # full simulation and check no checkpoints
        final_time_max = 20
        metadata = dict(max_time=final_time_max)
        final_time, final_state, final_random_state = mock_simulate(metadata=metadata,
                                                                    checkpoint_step=checkpoint_step)

        access_checkpoints = AccessCheckpoints(self.checkpoint_dir)
        self.assertEqual([], access_checkpoints.list_checkpoints(error_if_empty=False))
        with self.assertRaises(SimulatorError):
            access_checkpoints.list_checkpoints()
        self.assertGreaterEqual(final_time, final_time_max)

        # run simulation to check checkpointing
        max_time = 10
        metadata = dict(max_time=max_time)
        time, _, _ = mock_simulate(metadata=metadata, checkpoint_dir=self.checkpoint_dir,
                                   checkpoint_step=checkpoint_step)
        self.assertGreaterEqual(time, max_time)

        # check that checkpoints created and
        # list_checkpoints() reloads from updated self.checkpoint_dir
        self.assertTrue(sorted(access_checkpoints.list_checkpoints()))
        numpy.testing.assert_array_almost_equal(
            access_checkpoints.list_checkpoints(),
            numpy.linspace(0, max_time, int(1 + max_time / checkpoint_step)),
            decimal=1)

        # check that checkpoints have correct data
        checkpoint_time = 5
        chkpt = access_checkpoints.get_checkpoint(time=checkpoint_time)
        self.assertIn('time:', str(chkpt))
        self.assertIn('state:', str(chkpt))
        self.assertLessEqual(chkpt.time, checkpoint_time)

        chkpt = access_checkpoints.get_checkpoint()
        self.assertLessEqual(chkpt.time, max_time)

        # check that resumed simulation reproduces earlier run
        metadata = dict(max_time=final_time_max)
        time, state, random_state = mock_simulate(metadata=metadata,
                                                  init_time=chkpt.state.time,
                                                  init_state=chkpt.state.local_state,
                                                  init_checkpoint_time=chkpt.time,
                                                  init_random_state=chkpt.random_state,
                                                  checkpoint_dir=self.checkpoint_dir,
                                                  checkpoint_step=checkpoint_step)
        self.assertEqual(time, final_time)
        self.assertEqual(state, final_state)
        wc_utils.util.types.assert_value_equal(random_state, final_random_state,
                                               check_iterable_ordering=True)

        # check checkpoints created
        # access_checkpoints = AccessCheckpoints(self.checkpoint_dir)
        self.assertTrue(sorted(access_checkpoints.list_checkpoints()))
        numpy.testing.assert_array_almost_equal(
            access_checkpoints.list_checkpoints(),
            numpy.linspace(0, final_time_max, int(1 + final_time_max / checkpoint_step)),
            decimal=1)

        # check checkpoints have correct data
        chkpt = access_checkpoints.get_checkpoint()
        self.assertLessEqual(chkpt.time, final_time)


class MockAccessCheckpointsLogger(object):
    """ Create checkpoints at a uniform sequence of times

    Attributes:
        dirname (:obj:`str`): directory to write checkpoint data
        event_time_sequence (:obj:`UniformSequence`):
        _next_checkpoint (:obj:`float`): time in simulated time units of next checkpoint
    """

    def __init__(self, dirname, step, initial_time):
        """
        Args:
            dirname (:obj:`str`): directory to write checkpoint data
            step (:obj:`float`): simulation time between checkpoints in simulated time units
            initial_time (:obj:`float`): starting simulation time
        """
        self.event_time_sequence = UniformSequence(initial_time, step)
        self._next_checkpoint = self.event_time_sequence.__next__()
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        self.dirname = dirname

    def checkpoint_periodically(self, sim_time, local_state, random_state):
        """ Store all periodic checkpoint up through simulation time `sim_time`

        Args:
            sim_time (:obj:`float`): simulation time
            local_state (:obj:`object`): simulated local state
            random_state (:obj:`numpy.random.RandomState`): random number generator state
        """
        while self._next_checkpoint <= sim_time:
            self.checkpoint(self._next_checkpoint, FullSimulationState(sim_time, local_state), random_state)
            self._next_checkpoint = self.event_time_sequence.__next__()

    def checkpoint(self, time, full_state, random_state):
        """ Store checkpoint at time `time` with full state `full_state` and PRNG state `random_state`

        Args:
            time (:obj:`float`): simulation time
            full_state (:obj:`FullSimulationState`): simulated full state
            random_state (:obj:`numpy.random.RandomState`): random number generator state
        """
        access_checkpoints = AccessCheckpoints(self.dirname)
        access_checkpoints.set_checkpoint(Checkpoint(time, full_state, random_state.get_state()))


def mock_simulate(metadata, init_time=0, init_state=None, init_random_state=None, checkpoint_dir=None,
                  init_checkpoint_time=0, checkpoint_step=None):
    """ Run a mock simulation

    Advance time randomly, and checkpoint periodically. Allowed to run one iteration past `max_time`.

    Args:
        metadata (:obj:`dict`): metadata about the mock simulation
        init_time (:obj:`float`): simulation start time
        init_state (:obj:`object`): simulation initial state
        init_random_state (:obj:`random.RandomState`): simulation initial random state
        checkpoint_dir (:obj:`str`): simulation checkpoint directory
        init_checkpoint_time (:obj:`float`): checkpoint start time
        checkpoint_step (:obj:`float`): simulation checkpoint period
    """
    # initialize
    if init_state is None:
        state = 0
    else:
        state = init_state

    random_state = random.RandomState(seed=0)
    if init_random_state is not None:
        random_state.set_state(init_random_state)

    # simulate temporal dynamics
    time = init_time

    if checkpoint_dir:
        logger = MockAccessCheckpointsLogger(checkpoint_dir, checkpoint_step, init_checkpoint_time)

    while time < metadata['max_time']:
        # randomly advance time
        dt = random_state.exponential(1. / 100.)
        time += dt
        state += 1

        if checkpoint_dir:
            logger.checkpoint_periodically(time, state, random_state)

        if metadata['max_time'] <= time:
            break

    return (time, state, random_state.get_state())
