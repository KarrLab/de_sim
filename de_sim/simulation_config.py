""" Simulation configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
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


@dataclass
class SimulationConfig:
    """ Configuration information for a simulation run

    - Simulation start time
    - Simulation maximum time
    - Random number generator seed
    - Stop condition
    - Progress bar switch
    - Metadata directory

    Attributes:
        time_max (:obj:`float`): maximum simulation time
        time_init (:obj:`float`, optional): initial simulation time
        random_seed (:obj:`int`, optional): random number generator seed
        stop_condition (:obj:`function`, optional): if provided, a function that takes one argument,
            the simulation time; a simulation terminates if the function returns `True`
        progress (:obj:`bool`, optional): if `True`, output a bar that dynamically reports the
            simulation's progress
        metadata_dir (:obj:`str`, optional): directory for saving metadata; if not provided,
            then metatdata should be saved before another simulation is run with the same `SimulationEngine`
    """

    time_max: float
    time_init: float = 0.0
    random_seed: int = None
    stop_condition: object = None   # the type is 'function', but dataclass rejects it; check it below
    progress: bool = False
    metadata_dir: str = None

    def validate(self):
        # validate types
        for field in dataclasses.fields(self):
            attr = getattr(self, field.name)
            # dataclasses._MISSING_TYPE is the value used for default if no default is provided
            if 'dataclasses._MISSING_TYPE' in str(field.default):
                if not isinstance(attr, field.type):
                    raise SimulatorError(f"{field.name} ('{attr}') is not a(n) {field.type.__name__}")
            else:
                if (field.default is None and attr is not None) or field.default is not None:
                    if not isinstance(attr, field.type):
                        raise SimulatorError(f"{field.name} ('{attr}') is not a(n) {field.type.__name__}")

        # other validation
        if self.time_max <= self.time_init:
            raise SimulatorError(f'time_max ({self.time_max}) must be greater than time_init ({self.time_init})')

        # make sure stop_condition is a function
        if self.stop_condition is not None and not isinstance(self.stop_condition, types.FunctionType):
            raise SimulatorError(f"stop_condition ('{self.stop_condition}') is not a function")

        # ensure that metadata_dir is a directory
        if self.metadata_dir is not None and not Path(self.metadata_dir).is_dir():
            raise SimulatorError(f"metadata_dir ('{self.metadata_dir}') is not a directory")
