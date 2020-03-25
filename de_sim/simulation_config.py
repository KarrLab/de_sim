""" Simulation configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-16
:Copyright: 2020, Karr Lab
:License: MIT
"""

from dataclasses import dataclass
from pathlib import Path
import copy
import dataclasses
import math
import os
import types

from de_sim.errors import SimulatorError
from wc_utils.util.misc import ValidatedDataClass


@dataclass
class SimulationConfig(ValidatedDataClass):
    """ Configuration information for a simulation run

    - Simulation start time
    - Simulation maximum time
    - Stop condition
    - Progress bar switch
    - Data directory

    Attributes:
        time_max (:obj:`float`): maximum simulation time
        time_init (:obj:`float`, optional): time at which a simulation starts
        stop_condition (:obj:`function`, optional): if provided, a function that takes one argument,
            the simulation time; a simulation terminates if the function returns `True`
        progress (:obj:`bool`, optional): if `True`, output a bar that dynamically reports the
            simulation's progress
        output_dir (:obj:`str`, optional): directory for saving metadata; will be created if it does't
            exist; if not provided, then metatdata should be saved before another simulation is run
            with the same `SimulationEngine`
    """

    time_max: float
    time_init: float = 0.0
    stop_condition: object = None   # stop_condition must be callable, which is checked below
    progress: bool = False
    output_dir: str = None

    DO_NOT_PICKLE = ['stop_condition']

    def __setattr__(self, name, value):
        """ Validate an attribute when it is changed """
        try:
            super().__setattr__(name, value)
        except TypeError as e:
            raise SimulatorError(e)

    def validate_individual_fields(self):
        """ Validate constraints other than types in individual fields in a `SimulationConfig` instance

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

                # raise error if absolute_output_dir is not empty
                if os.listdir(absolute_output_dir):
                    raise SimulatorError(f"output_dir '{absolute_output_dir}' is not empty")

            # if absolute_output_dir does not exist, make it
            if not os.path.exists(absolute_output_dir):
                os.makedirs(absolute_output_dir)

            self.output_dir = absolute_output_dir

    def validate(self):
        """ Validate a `SimulationConfig` instance

        Validation tests that involve multiple fields must be made in this method. Call it after the
        `SimulationConfig` instance is in a consistent state.

        Returns:
            :obj:`None`: if no error is found

        Raises:
            :obj:`SimulatorError`: if `self` fails validation
        """

        self.validate_individual_fields()

        # other validation
        if self.time_max <= self.time_init:
            raise SimulatorError(f'time_max ({self.time_max}) must be greater than time_init ({self.time_init})')

    # FIX FOR DE-SIM CHANGES
    # TODO: make generic, auto-determining DO_NOT_PICKLE, & move to wc_utils.util.misc.ValidatedDataClass
    def prepare_to_pickle(self):
        """ Provide a copy that can be pickled

        Returns:
            :obj:`SimulationConfig`: a copy of `self` that can be pickled
        """
        to_pickle = copy.deepcopy(self)
        for field in dataclasses.fields(self):
            attr = getattr(self, field.name)
            if field.name in self.DO_NOT_PICKLE:
                setattr(to_pickle, field.name, None)
            elif isinstance(attr, ValidatedDataClass):
                setattr(to_pickle, field.name, attr.prepare_to_pickle())
        return to_pickle
