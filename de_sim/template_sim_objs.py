""" Template simulation objects

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-05-16
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

from de_sim.errors import SimulatorError
import de_sim


class NextEvent(de_sim.EventMessage):
    "Schedule the next event"


class TemplatePeriodicSimulationObject(de_sim.SimulationObject):
    """ Template self-clocking :obj:`~de_sim.simulation_object.SimulationObject`

    Events occur at time `start_time`, `start_time + period`, `start_time + 2*period`, ...

    To minimize roundoff errors in event times track the number of periods, and multiply by period
    to determine event times.

    Attributes:
        period (:obj:`float`): interval between events, in simulated time units
        num_periods (:obj:`int`): number of periods executed
        start_time (:obj:`float`, optional): the time of the first periodic event
    """

    def __init__(self, name, period, start_time=0.):
        if period <= 0:
            raise SimulatorError("period must be positive, but is {}".format(period))
        self.period = period
        self.start_time = start_time
        self.num_periods = 0
        super().__init__(name, start_time=start_time)

    def schedule_next_event(self):
        """ Schedule the next event in `self.period` simulated time units
        """
        next_event_time = self.start_time + self.num_periods * self.period
        self.num_periods += 1
        self.send_event_absolute(next_event_time, self, NextEvent())

    def handle_event(self, event):
        """ Handle the periodic event

        Derived classes which wish to process the event must override this method

        Args:
            event (:obj:`~de_sim.event.Event`): simulation event; not used
        """
        pass    # pragma: no cover     # must be overridden

    def init_before_run(self):
        """ Schedule the initial event
        """
        self.schedule_next_event()

    def handle_simulation_event(self, event):
        """ Handle the periodic event

        Args:
            event (:obj:`~de_sim.event.Event`): the simulation event

        Call `handle_event` and schedule the next event
        """
        self.handle_event(event)
        self.schedule_next_event()

    event_handlers = [(NextEvent, handle_simulation_event)]

    # register the message type sent
    messages_sent = [NextEvent]
