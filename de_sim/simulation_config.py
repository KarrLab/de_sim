""" Simulation configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2020-03-16
:Copyright: 2020, Karr Lab
:License: MIT
"""

from dataclasses import dataclass
from pathlib import Path
import dataclasses
import math
import os
import types

from de_sim.errors import SimulatorError


# TODO: FIX FOR DE-SIM CHANGES: move this & its tests to wc_utils as a generic class, and use here & in wc_sim
class ValidatedDataClass(object):
    """ A mixin that validates attributes in dataclasses
    """

    LIKELY_INITIAL_VOWEL_SOUNDS = {'a', 'e', 'i', 'o', 'u'}

    def validate_dataclass_type(self, attr_name):
        """ Validate the type of an attribute in a dataclass instance

        Args:
            attr_name (:obj:`str`): the name of the attribute to validate

        Returns:
            :obj:`None`: if no error is found

        Raises:
            :obj:`ValueError`: if `attr_name` is not the name of a field
            :obj:`TypeError`: if attribute `attr_name` does not have the right type
        """

        fields_map = {field.name: field for field in dataclasses.fields(self)}
        if attr_name not in fields_map:
            raise ValueError(f"'{attr_name}' must be a field in {self.__class__.__name__}")

        # validate type
        field = fields_map[attr_name]
        attr = getattr(self, field.name)

        # place the right article before a type name, approximately
        single_article = 'a'
        if field.type.__name__[0].lower() in self.LIKELY_INITIAL_VOWEL_SOUNDS:
            single_article = 'an'

        # accept int inputs to float fields
        if isinstance(attr, int) and field.type is float:
            attr = float(attr)
            setattr(self, field.name, attr)

        # dataclasses._MISSING_TYPE is the value used for default if no default is provided
        if 'dataclasses._MISSING_TYPE' in str(field.default):
            if not isinstance(attr, field.type):
                raise TypeError(f"{field.name} ('{attr}') must be {single_article} {field.type.__name__}")
        else:
            if (field.default is None and attr is not None) or field.default is not None:
                if not isinstance(attr, field.type):
                    raise TypeError(f"{field.name} ('{attr}') must be {single_article} {field.type.__name__}")

    def validate_dataclass_types(self):
        """ Validate the types of all attributes in a dataclass instance

        Returns:
            :obj:`None`: if no error is found

        Raises:
            :obj:`error_type`: if an attribute does not have the right type
        """

        # validate types
        for field in dataclasses.fields(self):
            self.validate_dataclass_type(field.name)

    def __setattr__(self, name, value):
        """ Validate an attribute when it is changed """
        object.__setattr__(self, name, value)
        self.validate_dataclass_type(name)


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
        data_dir (:obj:`str`, optional): directory for saving metadata; will be created if it does't
            exist; if not provided, then metatdata should be saved before another simulation is run
            with the same `SimulationEngine`
    """

    time_max: float
    time_init: float = 0.0
    stop_condition: object = None   # stop_condition must be callable, which is checked below
    progress: bool = False
    data_dir: str = None

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

        # validate data_dir and convert to absolute path
        if self.data_dir is not None:
            absolute_data_dir = os.path.abspath(os.path.expanduser(self.data_dir))

            if os.path.exists(absolute_data_dir):
                # raise error if absolute_data_dir exists and is not a dir
                if not os.path.isdir(absolute_data_dir):
                    raise SimulatorError(f"data_dir '{absolute_data_dir}' must be a directory")

                # raise error if absolute_data_dir is not empty
                if os.listdir(absolute_data_dir):
                    raise SimulatorError(f"data_dir '{absolute_data_dir}' is not empty")

            # if absolute_data_dir does not exist, make it
            if not os.path.exists(absolute_data_dir):
                os.makedirs(absolute_data_dir)

            self.data_dir = absolute_data_dir

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
