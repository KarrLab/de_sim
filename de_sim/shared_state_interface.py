""" An interface that all shared state objects must support

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-15
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

import abc


class SharedStateInterface(object, metaclass=abc.ABCMeta):  # pragma: no cover
    """ An ABC all shared state objects must support so they can participate in logs and checkpoints
    """

    @abc.abstractmethod
    def get_name(self):
        """ Get the shared state objects's name

        Returns:
            :obj:`str`: the name of a shared state object
        """
        pass

    @abc.abstractmethod
    def get_shared_state(self, time):
        """ Get the shared state objects's state

        Args:
            time (:obj:`float`): the simulation time of the state to be returned

        Returns:
            :obj:`str`: the state of a shared state object, in a human-readable string
        """
        pass
