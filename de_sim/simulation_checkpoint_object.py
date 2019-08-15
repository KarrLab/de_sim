""" A simulation object that produces periodic checkpoints

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-05-03
:Copyright: 2018, Karr Lab
:License: MIT
"""
import sys
import abc

from de_sim.simulation_message import SimulationMessage
from de_sim.simulation_object import ApplicationSimulationObject
from de_sim.errors import SimulatorError
from de_sim.checkpoint import Checkpoint
from de_sim.template_sim_objs import TemplatePeriodicSimulationObject


class AbstractCheckpointSimulationObject(TemplatePeriodicSimulationObject):
    """ Abstract class that creates periodic checkpoints

    Attributes:
        checkpoint_period (:obj:`float`): interval between checkpoints, in simulated seconds
    """

    def handle_event(self):
        self.create_checkpoint()

    def create_checkpoint(self):
        """ Create a checkpoint

        Derived classes must override this method and actually create a checkpoint
        """
        pass    # pragma: no cover     # must be overridden


class AccessStateObjectInterface(metaclass=abc.ABCMeta):
    """ An abstract base class that all access state objects must support
    """

    @abc.abstractmethod
    def get_checkpoint_state(self, time):
        """ Obtain a checkpoint of the simulation's model state at time `time`

        Returns:
            :obj:`object`: a checkpoint of the simulation's model state
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_random_state(self):
        """ Obtain a checkpoint of the state of the simulation's random number generator(s)

        Returns:
            :obj:`object`: the state of the simulation's random number generator(s)
        """
        pass  # pragma: no cover


class CheckpointSimulationObject(AbstractCheckpointSimulationObject):
    """ Create periodic checkpoints to files

    Attributes:
        checkpoint_dir (:obj:`str`): the directory in which to save checkpoints
        access_state_obj (:obj:`AccessStateObjectInterface`): an object whose `get_checkpoint_state(time)`
            returns the simulation's state at time `time`; `access_state_obj` objects should be derived from
            `AccessStateObjectInterface`
    """

    def __init__(self, name, checkpoint_period, checkpoint_dir, access_state_obj):
        self.checkpoint_dir = checkpoint_dir
        self.access_state_obj = access_state_obj
        super().__init__(name, checkpoint_period)

    def create_checkpoint(self):
        """ Create a checkpoint in the directory `self.checkpoint_dir`
        """
        Checkpoint.set_checkpoint(self.checkpoint_dir,
            Checkpoint(self.time, self.access_state_obj.get_checkpoint_state(self.time),
                self.access_state_obj.get_random_state()))
