""" Template simulation objects

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-05-16
:Copyright: 2018, Karr Lab
:License: MIT
"""

from de_sim.simulation_message import SimulationMessage
from de_sim.simulation_object import ApplicationSimulationObject
from de_sim.errors import SimulatorError
from wc_utils.util.uniform_seq import UniformSequence


class NextEvent(SimulationMessage):
    "Schedule the next event"


class TemplatePeriodicSimulationObject(ApplicationSimulationObject):
    """ Template self-clocking ApplicationSimulationObject

    Events occur at time 0, `period`, `2 x period`, ...

    To avoid roundoff errors in event times get them from a `UniformSequence`.

    Attributes:
        period (:obj:`float`): interval between events, in simulated seconds
        event_time_sequence (:obj:`UniformSequence`): a uniform sequence generator
    """

    def __init__(self, name, period):
        if period <= 0:
            raise SimulatorError("period must be positive, but is {}".format(period))
        self.period = period
        self.event_time_sequence = UniformSequence(0, period)
        super().__init__(name)

    def schedule_next_event(self):
        """ Schedule the next event in `self.period` simulated seconds
        """
        next_event_time = self.event_time_sequence.__next__()
        self.send_event_absolute(next_event_time, self, NextEvent())

    def handle_event(self):
        """ Handle the periodic event

        Derived classes must override this method and actually handle the event
        """
        pass    # pragma: no cover     # must be overridden

    def send_initial_events(self):
        # create the initial event
        self.schedule_next_event()

    def handle_simulation_event(self, event):
        self.handle_event()
        self.schedule_next_event()

    def get_state(self):
        return ''    # pragma: no cover

    event_handlers = [(NextEvent, handle_simulation_event)]

    # register the message type sent
    messages_sent = [NextEvent]
