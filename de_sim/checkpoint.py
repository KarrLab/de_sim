""" Checkpoints for a simulation run

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-08-30
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

from bisect import bisect
import math
import numpy
import os
import pickle
import re

from de_sim.config import core
from de_sim.errors import SimulatorError
from wc_utils.util.misc import obj_to_str

MAX_TIME_PRECISION = core.get_config()['de_sim']['max_time_precision']


class Checkpoint(object):
    """ Represents a simulation checkpoint

    Attributes:
        time (:obj:`float`): the checkpoint's simulated time, in simulation time units
        state (:obj:`object`): the simulation application's state at time `time`
        random_state (:obj:`object`): the state of the simulator's random number generator at time `time`
    """

    def __init__(self, time, state, random_state):
        self.time = time
        self.state = state
        self.random_state = random_state

    def __str__(self):
        """ Provide a human readable representation of this :obj:`Checkpoint`

        Returns:
            :obj:`str`: a human readable representation of this :obj:`Checkpoint`
        """

        return obj_to_str(self, ['time', 'state', 'random_state'])

    def __eq__(self, other):
        """ Compare two checkpoints

        Assumes that state objects implement the equality comparison operation `__eq__()`

        Args:
            other (:obj:`Checkpoint`): other checkpoint

        Returns:
            :obj:`bool`: :obj:`True` if checkpoints are semantically equal
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
            other (:obj:`Checkpoint`): other checkpoint

        Returns:
            :obj:`bool`: :obj:`True` if checkpoints are semantically unequal
        """
        return not self.__eq__(other)


class AccessCheckpoints(object):
    """ Represent a directory that contains the checkpoints from a simulation run

    Checkpoints are saved in pickle files, named `t.pickle`, where `t` is the simulation time
    of the checkpoint.

    Attributes:
        dir_path (:obj:`str`): the directory containing simulation checkpoints
        _last_dir_mod (:obj:`str`): most recent wall-clock time when the contents of `dir_path` were modified;
            used to avoid unnecessary updates to `all_checkpoints`
        all_checkpoints (:obj:`list` of :obj:`float`): sorted list of the simulation times of all
            checkpoints in `dir_path`
    """

    def __init__(self, dir_path):
        self.dir_path = dir_path
        self._last_dir_mod = os.stat(self.dir_path).st_mtime_ns
        self.all_checkpoints = None

    def set_checkpoint(self, checkpoint):
        """ Save a checkpoint in the directory `dir_path`

        Args:
            checkpoint (:obj:`Checkpoint`): checkpoint
        """
        file_name = self.get_filename(checkpoint.time)

        with open(file_name, 'wb') as file:
            pickle.dump(checkpoint, file)

    def get_checkpoint(self, time=None):
        """ Get the latest checkpoint in directory `dir_path` whose time is before or equal to `time`

        However, if no checkpoint with time <= `time` exists, then return the first checkpoint.
        If `time` is `None`, return the last checkpoint.

        For example, consider checkpoints at 1.0 s, 1.5 s, and 2.0 s. If `time` = 1.5 s, then
        return the checkpoint from 1.5 s. Return the same checkpoint if `time` = 1.9 s.
        But, if `time` = 0.9 s, the checkpoint from 1.0 s would be returned.
        And if `time` is `None`, return the checkpoint from 2.0 s.

        Args:
            time (:obj:`float`, optional): time in simulated time units of desired checkpoint; if not provided,
                the most recent checkpoint is returned

        Returns:
            :obj:`Checkpoint`: the most recent checkpoint before time `time`, or the most recent
            checkpoint if `time` is not provided
        """
        # get list of checkpoints
        checkpoint_times = self.list_checkpoints()

        # select closest checkpoint
        if time is None:
            nearest_time = checkpoint_times[-1]
        else:
            index = bisect(checkpoint_times, time) - 1
            index = max(index, 0)
            nearest_time = checkpoint_times[index]

        file_name = self.get_filename(nearest_time)

        # load and return this checkpoint
        with open(file_name, 'rb') as file:
            return pickle.load(file)

    def list_checkpoints(self, error_if_empty=True):
        """ Get sorted list of times of saved checkpoints in checkpoint directory `dir_path`

        To enhance performance the list of times is cached in attribute `all_checkpoints` and
        refreshed from the contents of directory `dir_path` if it has been updated.

        Args:
            error_if_empty (:obj:`bool`, optional): if set, report an error if no checkpoints are found

        Returns:
            :obj:`list` of :obj:`float`: sorted list of times of saved checkpoints

        Raises:
            :obj:`SimulatorError`: if `dirname` doesn't contain any checkpoints
        """
        # reload all_checkpoints if they have not been obtained
        # or self.dir_path has been modified since all_checkpoints was last obtained
        if self.all_checkpoints is None or self._last_dir_mod < os.stat(self.dir_path).st_mtime_ns:
            self._last_dir_mod = os.stat(self.dir_path).st_mtime_ns

            # find checkpoint times
            checkpoint_times = []
            pattern = r'^(\d+\.\d{' + f'{MAX_TIME_PRECISION},{MAX_TIME_PRECISION}' + r'})\.pickle$'
            for file_name in os.listdir(self.dir_path):
                match = re.match(pattern, file_name)
                if os.path.isfile(os.path.join(self.dir_path, file_name)) and match:
                    checkpoint_times.append(float(match.group(1)))

            # sort by time
            checkpoint_times.sort()

            self.all_checkpoints = checkpoint_times

        # error if no checkpoints found
        if error_if_empty and not self.all_checkpoints:
            raise SimulatorError("no checkpoints found in '{}'".format(self.dir_path))

        # return list of checkpoint times
        return self.all_checkpoints

    def get_filename(self, time):
        """ Get the filename for the checkpoint at time `time`

        Args:
            time (:obj:`float`): time

        Returns:
            :obj:`str`: filename for the checkpoint at time `time`
        """
        filename_time = f'{time:.{MAX_TIME_PRECISION}f}'
        if not math.isclose(float(filename_time), time):
            raise SimulatorError(f"filename time {filename_time} is not close to time {time}")
        return os.path.join(self.dir_path, f'{filename_time}.pickle')
