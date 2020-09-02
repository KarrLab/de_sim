""" Classes that represent the metadata of a simulation run

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

    All :obj:`RunMetadata` attributes are obtained automatically.

    Attributes:
        ip_address (:obj:`str`): IP address of the machine that ran the simulation
        start_time (:obj:`datetime`): clock start time when the simulation started
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

        Returns :obj:`False` if `other` is not a :obj:`RunMetadata`.
        Otherwise, always returns :obj:`True` , because a simulation's results do not depend on the data
        in its :obj:`RunMetadata`.

        Args:
            other (:obj:`Object`): other object

        Returns:
            :obj:`bool`: :obj:`True` if `other` is a :obj:`RunMetadata`
        """
        return isinstance(other, RunMetadata)


@dataclass
class AuthorMetadata(EnhancedDataClass):
    """ Represents a simulation's author

    If possible, the author's username is obtained automatically. All other attributes must be set manually.

    Attributes:
        name (:obj:`str`): the author's name
        email (:obj:`str`): the author's email address
        username (:obj:`str`): the author's username
        organization (:obj:`str`): the author's organization
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
    """ Represent the metadata of a simulation run; incorporates four types of metadata classes

    Attributes:
        simulation_config (:obj:`~de_sim.simulation_config.SimulationConfig`): information about the
            simulation's configuration (e.g. start time, maximum time)
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
        """ Get the pathname for a pickled :obj:`SimulationMetadata` object stored in directory `dirname`

        Args:
            dirname (:obj:`str`): directory that stores a pickled representation of a :obj:`SimulationMetadata` object

        Returns:
            :obj:`str`: pathname to a pickled file storing a :obj:`SimulationMetadata` object
        """
        return os.path.join(dirname, 'simulation_metadata.pickle')

    def __setattr__(self, name, value):
        """ Validate an attribute in this :obj:`SimulationMetadata` when it is changed

        Overrides `__setattr__` in :obj:`EnhancedDataClass` to report errors as :obj:`~de_sim.errors.SimulatorError`\ s
        """
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
        return (isinstance(other, SimulationMetadata) and
                self.simulation_config.semantically_equal(other.simulation_config) and
                self.author.semantically_equal(other.author) and
                # RepositoryMetadata doesn't define semantically_equal because it is not an EnhancedDataClass
                self.simulator_repo == other.simulator_repo)
