""" Simulation configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-16
:Copyright: 2020, Karr Lab
:License: MIT
"""

from dataclasses import dataclass
import os

from de_sim.checkpoint import AccessCheckpoints
from de_sim.errors import SimulatorError
from wc_utils.util.misc import EnhancedDataClass


@dataclass
class SimulationConfig(EnhancedDataClass):
    """ A dataclass that holds configuration information for a simulation run

    - Simulation maximum time
    - Simulation start time
    - Stop condition
    - Directory for storing simulation metadata
    - Progress bar switch
    - Performance profiling switch
    - Configure profiling of heap memory use

    Attributes:
        max_time (:obj:`float`): maximum simulation time
        time_init (:obj:`float`, optional): time at which a simulation starts; defaults to 0
        stop_condition (:obj:`function`, optional): if provided, a function that takes one argument,
            the simulation time; a simulation terminates if the function returns `True`
        output_dir (:obj:`str`, optional): directory for saving metadata; `output_dir` will be created if it does't
            exist; if not provided, then metadata should be saved before another simulation is run
            with the same :obj:`~de_sim.simulator.Simulator`
        progress (:obj:`bool`, optional): if `True`, output a text bar that dynamically reports a
            simulation's progress
        profile (:obj:`bool`, optional): if `True`, output a profile of the simulation's performance
            created by a Python profiler
        object_memory_change_interval (:obj:`int`, optional): number of simulation events between reporting
            changes in heap object count and memory use; if 0 do not report; defaults to do not report;
            cannot be used with `profile` as they run much too slowly
    """

    max_time: float
    time_init: float = 0.0
    stop_condition: object = None   # stop_condition must be callable, which is checked below
    output_dir: str = None
    progress: bool = False
    profile: bool = False
    object_memory_change_interval: int = 0
    DO_NOT_PICKLE = ['stop_condition']

    def __setattr__(self, name, value):
        """ Validate an attribute in this :obj:`SimulationConfig` when it is changed

        Overrides `__setattr__` in :obj:`EnhancedDataClass` to report errors as :obj:`~de_sim.errors.SimulatorError`\ s
        """
        try:
            super().__setattr__(name, value)
        except TypeError as e:
            raise SimulatorError(e)

    def validate_individual_fields(self):
        """ Validate constraints on individual fields in a :obj:`SimulationConfig` instance

        Returns:
            :obj:`None`: if no error is found

        Raises:
            :obj:`SimulatorError`: if an attribute of `self` fails validation
        """

        # make sure stop_condition is callable
        if self.stop_condition is not None and not callable(self.stop_condition):
            raise SimulatorError(f"stop_condition ('{self.stop_condition}') must be a function")

        # validate output_dir and convert to absolute path
        if self.output_dir is not None:
            absolute_output_dir = os.path.abspath(os.path.expanduser(self.output_dir))

            if os.path.exists(absolute_output_dir):
                # raise error if absolute_output_dir exists and is not a dir
                if not os.path.isdir(absolute_output_dir):
                    raise SimulatorError(f"output_dir '{absolute_output_dir}' must be a directory")

                # prevent output from multiple simulation runs in an output directory
                if AccessCheckpoints(absolute_output_dir).list_checkpoints(error_if_empty=False):
                    raise SimulatorError(f"output_dir '{absolute_output_dir}' already contains checkpoints")

            # if absolute_output_dir does not exist, make it
            if not os.path.exists(absolute_output_dir):
                os.makedirs(absolute_output_dir)

            self.output_dir = absolute_output_dir

        # make sure object_memory_change_interval is non-negative
        if self.object_memory_change_interval < 0:
            raise SimulatorError(f"object_memory_change_interval ('{self.object_memory_change_interval}') "
                                 "must be non-negative")

    def validate(self):
        """ Validate a `SimulationConfig` instance

        Validation tests that involve multiple fields are contained in this method.

        Returns:
            :obj:`None`: :obj:`None` if no error is found

        Raises:
            :obj:`SimulatorError`: if `self` fails validation
        """

        self.validate_individual_fields()

        # other validation
        if self.max_time <= self.time_init:
            raise SimulatorError(f'max_time ({self.max_time}) must be greater than time_init ({self.time_init})')

        if self.profile and 0 < self.object_memory_change_interval:
            raise SimulatorError('profile and object_memory_change_interval cannot both be active, '
                                 'as the combination slows DE Sim dramatically')

    def semantically_equal(self, other):
        """ Are two instances semantically equal with respect to a simulation's predictions?

        Overrides `semantically_equal` in :obj:`EnhancedDataClass`.
        The only attributes that are semantically meaningful to a simulation's predictions are
        `max_time` and `time_init`. Although they're floats, they are compared exactly because
        they're simulation inputs, not computed outputs.

        Args:
            other (:obj:`Object`): other object

        Returns:
            :obj:`bool`: :obj:`True` if `other` is a :obj:`SimulationConfig` that is semantically equal to `self`,
            :obj:`False` otherwise
        """
        return (isinstance(other, SimulationConfig) and self.max_time == other.max_time and
                self.time_init == other.time_init)
