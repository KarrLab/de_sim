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
import types

from de_sim.errors import SimulatorError


# NOW: TODO: move this to wc_utils as a generic class, and use here & in wc_sim
class ValidatedDataClass(object):
    """ A mixin that validates attributes in dataclasses
    """

    LIKELY_INITIAL_VOWEL_SOUNDS = {'a', 'e', 'i', 'o', 'u'}

    def validate_dataclass_types(self):
        """ Validate the types of all attributes in a dataclass instance

        Returns:
            :obj:`None`: if no error is found

        Raises:
            :obj:`error_type`: if an attribute does not have the right type
        """

        # validate types
        for field in dataclasses.fields(self):
            attr = getattr(self, field.name)

            # place the right article before a type name, approximately
            single_article = 'a'
            if field.name[0].lower() in self.LIKELY_INITIAL_VOWEL_SOUNDS:
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

    def __setattr__(self, name, value):
        """ Validate after each change to an attribute """
        object.__setattr__(self, name, value)
        self.validate_individual_fields()

    def validate_individual_fields(self):
        """ Validate individual fields

        Returns:
            :obj:`None`: if no error is found

        Raises:
            :obj:`Exception`: if an attribute of `self` fails validation
        """

        self.validate_dataclass_types()


@dataclass
class SimulationConfig(ValidatedDataClass):
    """ Configuration information for a simulation run

    - Simulation start time
    - Simulation maximum time
    - Stop condition
    - Progress bar switch
    - Metadata directory

    Attributes:
        time_max (:obj:`float`): maximum simulation time
        time_init (:obj:`float`, optional): time at which a simulation starts
        stop_condition (:obj:`function`, optional): if provided, a function that takes one argument,
            the simulation time; a simulation terminates if the function returns `True`
        progress (:obj:`bool`, optional): if `True`, output a bar that dynamically reports the
            simulation's progress
        metadata_dir (:obj:`str`, optional): directory for saving metadata; if not provided,
            then metatdata should be saved before another simulation is run with the same `SimulationEngine`
    """

    time_max: float
    time_init: float = 0.0
    stop_condition: object = None   # stop_condition must be callable, which is checked below
    progress: bool = False
    metadata_dir: str = None

    def validate_individual_fields(self):
        """ Validate individual fields in a `SimulationConfig` instance

        Returns:
            :obj:`None`: if no error is found

        Raises:
            :obj:`SimulatorError`: if an attribute of `self` fails validation
        """

        try:
            self.validate_dataclass_types()
        except TypeError as e:
            raise SimulatorError(e)

        # make sure stop_condition is callable
        if self.stop_condition is not None and not callable(self.stop_condition):
            raise SimulatorError(f"stop_condition ('{self.stop_condition}') must be a function")

        # ensure that metadata_dir is a directory
        if self.metadata_dir is not None and not Path(self.metadata_dir).is_dir():
            raise SimulatorError(f"metadata_dir ('{self.metadata_dir}') must be a directory")

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
