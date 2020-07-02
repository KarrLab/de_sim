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
        run_time (:obj:`float`): simulation run time in real seconds
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

    def semantically_equal(self, other):
        """ Evaluate whether two instances of :obj:`RunMetadata` are semantically equal

        Always returns :obj:`True`, because none of the attributes in :obj:`RunMetadata` are important
        to a simulations' results

        Args:
            other (:obj:`Object`): other object

        Returns:
            :obj:`bool`: :obj:`True`
        """
        return True


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

    def semantically_equal(self, other):
        """ Are two instances semantically equal with respect to a simulation's predictions?

        Overrides `semantically_equal` in :obj:`EnhancedDataClass`.
        Ignore run, as a :obj:`RunMetadata` is not semantically meaningful to a simulation's predictions
        and depends on a simulation's performance.

        Args:
            other (:obj:`Object`): other object

        Returns:
            :obj:`bool`: :obj:`True` if `other` is semantically equal to `self`, :obj:`False` otherwise
        """
        return self.simulation_config.semantically_equal(other.simulation_config) and \
            self.author.semantically_equal(other.author) and \
            self.simulator_repo == other.simulator_repo # RepositoryMetadata not an EnhancedDataClass,
                                                        # so it doesn't define semantically_equal()
