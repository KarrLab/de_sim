""" Classes to represent the metadata of a simulation run

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-08-18
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import datetime
import os
import socket
import warnings
import pickle
from abc import ABC, abstractmethod

import wc_utils.util.git
from wc_utils.util.misc import obj_to_str


class Comparable(ABC):
    """ Interface to an object that can be compared, for simulation metadata elements
    """
    @abstractmethod
    def __eq__(self, other):
        """ Compare two simulation metadata elements

        Args:
            other (:obj:`Comparable`): other simulation metadata element

        Returns:
            :obj:`bool`: true if simulation metadata elements are semantically equal
        """
        pass    # pragma: no cover

    @abstractmethod
    def __ne__(self, other):
        """ Compare two simulation metadata elements

        Args:
            other (:obj:`Comparable`): other simulation metadata element

        Returns:
            :obj:`bool`: true if simulation metadata objects are semantically unequal
        """
        pass    # pragma: no cover


class SimulationMetadata(object):
    """ Represents the metadata of a simulation run

    Attributes:
        model (:obj:`wc_utils.util.git.RepositoryMetadata`): Metadata about the model's git repository
        simulation (:obj:`object`): Information about the simulation's
            configuration (e.g. perturbations, random seed)
        run (:obj:`RunMetadata`): Information about the simulation's run (e.g. start time, duration)
        author (:obj:`AuthorMetadata`): Information about the person who ran the simulation
            (e.g. name, email)
    """
    ATTRIBUTES = ['model', 'simulation', 'run', 'author']

    def __init__(self, model, simulation, run, author):
        self.model = model
        self.simulation = simulation
        self.run = run
        self.author = author

    @staticmethod
    def write_metadata(simulation_metadata, dirname):
        """ Save a simulation metadata object to the directory `dirname`

        Args:
            simulation_metadata (:obj:`SimulationMetadata`): a simulation metadata instance
            dirname (:obj:`str`): directory for holding the metadata
        """

        file_name = SimulationMetadata.get_file_name(dirname)

        with open(file_name, 'wb') as file:
            pickle.dump(simulation_metadata, file)

    @staticmethod
    def read_metadata(dirname):
        """ Read a simulation metadata object from the directory `dirname`

        Args:
            dirname (:obj:`str`): directory for holding the metadata
        """

        file_name = SimulationMetadata.get_file_name(dirname)

        # load and return this simulation metadata
        with open(file_name, 'rb') as file:
            return pickle.load(file)

    def get_file_name(dirname):
        """ Get file name for simulation metadata stored in directory `dirname`

        Args:
            dirname (:obj:`str`): directory for holding the metadata

        Returns:
            :obj:`str`: file name for simulation metadata
        """

        return os.path.join(dirname, 'sim_metadata.pickle')

    def __eq__(self, other):
        """ Compare two simulation metadata objects

        Args:
            other (:obj:`SimulationMetadata`): other simulation metadata object

        Returns:
            :obj:`bool`: true if simulation metadata objects are semantically equal
        """
        if other.__class__ is not self.__class__:
            return False

        for attr in self.ATTRIBUTES:
            if getattr(other, attr) != getattr(self, attr):
                return False

        return True

    def __ne__(self, other):
        """ Compare two simulation metadata objects

        Args:
            other (:obj:`SimulationMetadata`): other simulation metadata object

        Returns:
            :obj:`bool`: true if simulation metadata objects are semantically unequal
        """
        return not self.__eq__(other)

    def __str__(self):
        """ Provide a readable representation of this `SimulationMetadata`

        Returns:
            :obj:`str`: a readable representation of this `SimulationMetadata`
        """
        return obj_to_str(self, self.ATTRIBUTES)


class RunMetadata(object):
    """ Represent a simulation's run

    Attributes:
        start_time (:obj:`datetime.datetime`): simulation start time
        run_time (:obj:`float`): simulation run time in seconds
        ip_address (:obj:`str`): ip address of the machine that ran the simulation
    """
    ATTRIBUTES = ['start_time', 'run_time', 'ip_address',]

    def __init__(self, start_time=None, run_time=None, ip_address=None):
        """ Construct a representation of simulation run

        Args:
            start_time (:obj:`datetime.datetime`): simulation start time
            run_time (:obj:`float`): simulation run time in seconds
            ip_address (:obj:`str`): ip address of the machine that ran the simulation
        """

        self.start_time = start_time
        self.run_time = run_time
        self.ip_address = ip_address

    def record_start(self):
        self.start_time = datetime.datetime.now()

    def record_end(self):
        self.run_time = (datetime.datetime.now() - self.start_time).total_seconds()

    def record_ip_address(self):
        self.ip_address = socket.gethostbyname(socket.gethostname())

    def __eq__(self, other):
        """ Compare two run metadata objects

        Args:
            other (:obj:`RunMetadata`): other run metadata object

        Returns:
            :obj:`bool`: true if run metadata objects are semantically equal
        """
        if other.__class__ is not self.__class__:
            return False

        for attr in self.ATTRIBUTES:
            if getattr(other, attr) != getattr(self, attr):
                return False

        return True

    def __ne__(self, other):
        """ Compare two run metadata objects

        Args:
            other (:obj:`RunMetadata`): other run metadata object

        Returns:
            :obj:`bool`: true if run metadata objects are semantically unequal
        """
        return not self.__eq__(other)

    def __str__(self):
        """ Provide a readable representation of this `RunMetadata`

        Returns:
            :obj:`str`: a readable representation of this `RunMetadata`
        """
        return obj_to_str(self, self.ATTRIBUTES)


class AuthorMetadata(object):
    """ Represents a simulation's author

    Attributes:
        name (:obj:`str`): authors' name
        email (:obj:`str`): author's email address
        username (:obj:`str`): authors' username
        organization (:obj:`str`): author's organization
    """
    ATTRIBUTES = ['name', 'email', 'username', 'organization']

    def __init__(self, name, email, username, organization):
        """ Construct a representation of the author of a simulation run

        Args:
            name (:obj:`str`): authors' name
            email (:obj:`str`): author's email address
            username (:obj:`str`): authors' username
            organization (:obj:`str`): author's organization
        """
        self.name = name
        self.email = email
        self.username = username
        self.organization = organization

    def __eq__(self, other):
        """ Compare two author metadata objects

        Args:
            other (:obj:`AuthorMetadata`): other author metadata object

        Returns:
            :obj:`bool`: true if author metadata objects are semantically equal
        """
        if other.__class__ is not self.__class__:
            return False

        for attr in self.ATTRIBUTES:
            if getattr(other, attr) != getattr(self, attr):
                return False

        return True

    def __ne__(self, other):
        """ Compare two author metadata objects

        Args:
            other (:obj:`AuthorMetadata`): other author metadata object

        Returns:
            :obj:`bool`: true if author metadata objects are semantically unequal
        """
        return not self.__eq__(other)

    def __str__(self):
        """ Provide a readable representation of this `AuthorMetadata`

        Returns:
            :obj:`str`: a readable representation of this `AuthorMetadata`
        """
        return obj_to_str(self, self.ATTRIBUTES)
