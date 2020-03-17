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
        _time_max (:obj:`float`): maximum simulation time
        _time_init (:obj:`float`, optional): initial simulation time
        _random_seed (:obj:`int`, optional): random number generator seed
        _stop_condition (:obj:`function`, optional): if provided, a function that takes one argument,
            the simulation time; a simulation terminates if the function returns `True`
        _progress (:obj:`bool`, optional): if `True`, output a bar that dynamically reports the
            simulation's progress
        _metadata_dir (:obj:`str`, optional): directory for saving metadata; if not provided,
            then metatdata should be saved before another simulation is run with the same `SimulationEngine`
    """

    _time_max: float
    _time_init: float = 0.0
    _random_seed: int = None
    _stop_condition: object = None   # _stop_condition must be callable, which is checked below
    _progress: bool = False
    _metadata_dir: str = None

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
        if self._time_max <= self._time_init:
            raise SimulatorError(f'time_max ({self._time_max}) must be greater than time_init ({self._time_init})')

        # make sure stop_condition is a function
        if self._stop_condition is not None and not callable(self._stop_condition):
            raise SimulatorError(f"stop_condition ('{self._stop_condition}') is not a function")

        # ensure that metadata_dir is a directory
        if self._metadata_dir is not None and not Path(self._metadata_dir).is_dir():
            raise SimulatorError(f"metadata_dir ('{self._metadata_dir}') is not a directory")

    # getters and setters for all attributes
    @property
    def time_max(self):
        return self._time_max

    @time_max.setter
    def time_max(self, value):
        self._time_max = value
        self.validate()

    @property
    def time_init(self):
        return self._time_init

    @time_init.setter
    def time_init(self, value):
        self._time_init = value
        self.validate()

    @property
    def random_seed(self):
        return self._random_seed

    @random_seed.setter
    def random_seed(self, value):
        self._random_seed = value
        self.validate()

    @property
    def stop_condition(self):
        return self._stop_condition

    @stop_condition.setter
    def stop_condition(self, value):
        self._stop_condition = value
        self.validate()

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value
        self.validate()

    @property
    def metadata_dir(self):
        return self._metadata_dir

    @metadata_dir.setter
    def metadata_dir(self, value):
        self._metadata_dir = value
        self.validate()
