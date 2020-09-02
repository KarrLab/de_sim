""" An interface for a mock simulation object that can evaluate unit test assertions

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-06
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

from unittest import TestCase

import de_sim


class MockSimulationObject(de_sim.SimulationObject):
    """ An object that helps test simulation objects
    """

    def __init__(self, name, test_case, **kwargs):
        """ Init a MockSimulationObject that can unittest a :obj:`~de_sim.simulation_object.SimulationObject`\ s behavior

        Use `self.test_case` and `self.kwargs` to evaluate unit tests

        Args:
            name (:obj:`str`): name for the :obj:`~de_sim.simulation_object.SimulationObject`
            test_case (:obj:`TestCase`): reference to the `TestCase` that launches the simulation
            kwargs (:obj:`dict`): arguments used by a test case
        """
        if not isinstance(test_case, TestCase):
            raise ValueError("'test_case' should be a unittest.TestCase instance, but it is a {}".format(
                type(test_case)))
        (self.test_case, self.kwargs) = (test_case, kwargs)
        super().__init__(name)

    # use 'abstract' to indicate that this class should not be instantiated
    abstract = True
    messages_sent = []
