""" Checkpointing log

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-08-30
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import math
import numpy
from bisect import bisect
import os
import pickle
import re

from wc_utils.util.misc import obj_to_str


class Checkpoint(object):
    """ Represents a simulation checkpoint

    Attributes:
        time (:obj:`float`): the checkpoint's simulated time, in sec
        state (:obj:`object`): the simulated model's state at time `time`
        random_state (:obj:`object`): the state of the simulator's random number generator at time `time`
    """

    def __init__(self, time, state, random_state):
        self.time = time
        self.state = state
        self.random_state = random_state

    @staticmethod
    def set_checkpoint(dirname, checkpoint):
        """ Save a checkpoint to the directory `dirname`.

        Args:
            checkpoint (:obj:`Checkpoint`): checkpoint
            dirname (:obj:`str`): directory to read/write checkpoint data
        """
        file_name = Checkpoint.get_file_name(dirname, checkpoint.time)

        with open(file_name, 'wb') as file:
            pickle.dump(checkpoint, file)

    @staticmethod
    def get_checkpoint(dirname, time=None):
        """ Get the latest checkpoint in directory `dirname` with time before or equal to `time`

        For example, consider checkpoints at 1.0 s, 1.5 s, and 2.0 s. If `time` = 1.5 s, then
        return the checkpoint from 1.5 s. Return the same checkpoint if `time` = 1.9 s.
        If no checkpoint with time <= `time` exists, then return the first checkpoint. E.g., if
        `time` = 0.9 s, the checkpoint from 1.0 s would be returned.
        Finally, if `time` is `None`, return the last checkpoint.

        Args:
            dirname (:obj:`str`): directory to read/write checkpoint data
            time (:obj:`float`, optional): time in seconds of desired checkpoint; if not provided,
                the most recent checkpoint is returned

        Returns:
            :obj:`Checkpoint`: the most recent checkpoint before time `time`, or the most recent
                checkpoint if `time` is not provided
        """
        # get list of checkpoints
        checkpoint_times = Checkpoint.list_checkpoints(dirname)

        # select closest checkpoint
        if time is None:
            nearest_time = checkpoint_times[-1]
        else:
            index = bisect(checkpoint_times, time) - 1
            index = max(index, 0)
            nearest_time = checkpoint_times[index]

        file_name = Checkpoint.get_file_name(dirname, nearest_time)

        # load and return this checkpoint
        with open(file_name, 'rb') as file:
            return pickle.load(file)

    @staticmethod
    def list_checkpoints(dirname, error_if_empty=True):
        """ Get sorted list of times of saved checkpoints in checkpoint directory `dirname`.

        Args:
            dirname (:obj:`str`): directory to read/write checkpoint data
            error_if_empty (:obj:`bool`, optional): if set, report an error if no checkpoints found

        Returns:
            :obj:`list`: sorted list of times of saved checkpoints

        Raises:
            :obj:`ValueError`: if `dirname` doesn't contain any checkpoints
        """
        # find checkpoint times
        checkpoint_times = []
        for file_name in os.listdir(dirname):
            match = re.match(r'^(\d+\.\d{6,6}).pickle$', file_name)
            if os.path.isfile(os.path.join(dirname, file_name)) and match:
                checkpoint_times.append(float(match.group(1)))

        # error if no checkpoints found
        if error_if_empty and not checkpoint_times:
            raise ValueError("no checkpoints found in '{}'".format(dirname))

        # sort by time
        checkpoint_times.sort()

        # return list of checkpoint times
        return checkpoint_times

    @staticmethod
    def get_file_name(dirname, time):
        """ Get file name for checkpoint at time `time`

        Args:
            dirname (:obj:`str`): directory to read/write checkpoint data
            time (:obj:`float`): time in seconds

        Returns:
            :obj:`str`: file name for checkpoint at time `time`
        """
        return os.path.join(dirname, '{:0.6f}.pickle'.format(math.floor(time * 1e6) / 1e6))

    def __str__(self):
        """ Provide a human readable representation of this `Checkpoint`

        Returns:
            :obj:`str`: a human readable representation of this `Checkpoint`
        """

        return obj_to_str(self, ['time', 'state', 'random_state'])

    def __eq__(self, other):
        """ Compare two checkpoints

        Assumes that state objects implement the equality comparison operation `__eq__()`

        Args:
            other (:obj:`checkpoint`): other checkpoint

        Returns:
            :obj:`bool`: true if checkpoints are semantically equal
        """
        if other.__class__ is not self.__class__:
            return False

        if other.time != self.time:
            return False

        if other.state != self.state:
            return False

        try:
            numpy.testing.assert_equal(other.random_state, self.random_state)
        except AssertionError:
            return False

        return True

    def __ne__(self, other):
        """ Compare two checkpoints

        Args:
            other (:obj:`checkpoint`): other checkpoint

        Returns:
            :obj:`bool`: true if checkpoints are semantically unequal
        """
        return not self.__eq__(other)


class CheckpointLogger(object):
    """ Checkpoint logger

    Attributes:
        dirname (:obj:`str`): directory to write checkpoint data
        step (:obj:`float`): simulation time between checkpoints in seconds
        _next_checkpoint (:obj:`float`): time in seconds of next checkpoint
    """

    def __init__(self, dirname, step, initial_time):
        """
        Args:
            dirname (:obj:`str`): directory to write checkpoint data
            step (:obj:`float`): simulation time between checkpoints in seconds
            initial_time (:obj:`float`): starting simulation time
        """
        next_checkpoint = math.ceil(initial_time / step) * step
        if next_checkpoint == initial_time:
            next_checkpoint += step

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        self.dirname = dirname
        self.step = step
        self._next_checkpoint = next_checkpoint

    def checkpoint_periodically(self, time, state, random_state):
        """ Periodically store checkpoint

        Args:
            time (:obj:`float`): simulation time in seconds
            state (:obj:`object`): simulated state (e.g. species counts)
            random_state (:obj:`numpy.random.RandomState`): random number generator state
        """
        if time >= self._next_checkpoint:
            self.checkpoint(time, state, random_state)
            self._next_checkpoint += self.step

    def checkpoint(self, time, state, random_state):
        """ Store checkpoint at time `time` with state `state` and ranodom number generator state `random_state`

        Args:
            time (:obj:`float`): simulation time in seconds
            state (:obj:`object`): simulated state (e.g. species counts)
            random_state (:obj:`numpy.random.RandomState`): random number generator state
        """
        Checkpoint.set_checkpoint(self.dirname, Checkpoint(time, state, random_state.get_state()))
