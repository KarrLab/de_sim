"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-15
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

from de_sim.simulation_object import ApplicationSimulationObject, SimObjClassPriority
from de_sim.testing.some_message_types import InitMsg, Eg1

ALL_MESSAGE_TYPES = [InitMsg, Eg1]
TEST_SIM_OBJ_STATE = 'Test SimulationObject state'


class ExampleSimulationObject(ApplicationSimulationObject):

    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def send_initial_events(self, *args):
        pass  # pragma: no cover

    def get_state(self):
        return TEST_SIM_OBJ_STATE

    def handler(self, event):
        pass  # pragma: no cover

    # register the event handler for each type of message received
    event_handlers = [(sim_msg_type, 'handler') for sim_msg_type in ALL_MESSAGE_TYPES]

    # register the message types sent
    messages_sent = ALL_MESSAGE_TYPES

    # have `ExampleSimulationObject`\ s execute at high priority
    class_priority = SimObjClassPriority.HIGH


class ImproperlyRegisteredSimulationObject(ApplicationSimulationObject):

    # register the event handler for each type of message received
    event_handlers = [(Eg1, 'handler')]

    # register the message types sent
    messages_sent = [InitMsg]

    def send_initial_events(self, *args):
        pass  # pragma: no cover

    def get_state(self):
        pass  # pragma: no cover

    def handler(self, event):
        pass  # pragma: no cover
