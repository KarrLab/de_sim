""" Classes to represent the metadata of a simulation run

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-18
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

from dataclasses import dataclass
from datetime import datetime
import getpass
import os
import socket

from de_sim.errors import SimulatorError
from de_sim.simulation_config import SimulationConfig
from wc_utils.util.misc import EnhancedDataClass
from wc_utils.util.git import RepositoryMetadata


@dataclass
class RunMetadata(EnhancedDataClass):
    """ Represent a simulation's run

    Attributes:
        ip_address (:obj:`str`): ip address of the machine that ran the simulation
        start_time (:obj:`datetime`): simulation clock start time
        run_time (:obj:`float`): simulation run time in seconds
    """

    ip_address: str = None
    start_time: datetime = None
    run_time: float = None

    def record_ip_address(self):
        self.ip_address = socket.gethostbyname(socket.gethostname())

    def record_start(self):
        self.start_time = datetime.now()

    def record_run_time(self):
        self.run_time = (datetime.now() - self.start_time).total_seconds()

    def __setattr__(self, name, value):
        """ Validate an attribute when it is changed """
        try:
            super().__setattr__(name, value)
        except TypeError as e:
            raise SimulatorError(e)


@dataclass
class AuthorMetadata(EnhancedDataClass):
    """ Represents a simulation's author

    Attributes:
        name (:obj:`str`): authors' name
        email (:obj:`str`): author's email address
        username (:obj:`str`): authors' username
        organization (:obj:`str`): author's organization
    """

    name: str = None
    email: str = None
    username: str = None
    organization: str = None

    def __post_init__(self):

        if self.username is None:
            try:
                self.username = getpass.getuser()
            except Exception:    # pragma: no cover
                self.username = None

    def __setattr__(self, name, value):
        """ Validate an attribute when it is changed """
        try:
            super().__setattr__(name, value)
        except TypeError as e:
            raise SimulatorError(e)


# TODO(Arthur): exact caching: implement __eq__, ignore run
@dataclass
class SimulationMetadata(EnhancedDataClass):
    """ Represents the metadata of a discrete event simulation run

    Attributes:
        simulation_config (:obj:`SimulationConfig`): information about the simulation's configuration
            (e.g. start time, maximum time)
        run (:obj:`RunMetadata`): information about the simulation's run (e.g. start time, duration)
        author (:obj:`AuthorMetadata`): information about the person who ran the simulation
            (e.g. name, email)
        simulator (:obj:`RepositoryMetadata`): metadata about this simulator's git repository
    """

    simulation_config: SimulationConfig
    run: RunMetadata
    author: AuthorMetadata
    simulator_repo: RepositoryMetadata = None

    @staticmethod
    def get_pathname(dirname):
        """ See docstring in :obj:`EnhancedDataClass`
        """
        return os.path.join(dirname, 'simulation_metadata.pickle')

    def __setattr__(self, name, value):
        """ Validate an attribute when it is changed """
        try:
            super().__setattr__(name, value)
        except TypeError as e:
            raise SimulatorError(e)
