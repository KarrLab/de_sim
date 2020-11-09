""" Simulation event class

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-05-31
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

from wc_utils.util.misc import round_direct
from wc_utils.util.list import elements_to_str


class Event(object):
    """ An object that holds a discrete-event simulation (DES) event

    Each DES event is scheduled by creating an :obj:`Event` instance and storing it in the
    simulator's event queue.

    As per David Jefferson's thinking, the event queue is ordered by data provided by the
    simulation application, in particular (event time, sub-time), where `sub-time` determines the
    execution priority among simultaneous messages with the same event time at different simulation
    objects.
    In `de_sim`, `sub-time` is a pair: the class priority for the receiving object, and a tiebreaker which
    is a unique value for each instance of the receiving object's class.
    This is implemented by the comparison operators for :obj:`Event` below. This ordering achieves
    deterministic and reproducible simulations. (For more theory, see Jefferson's LLNL course.)

    Attributes:
        creation_time (:obj:`float`): simulation time when the event is created (aka `send_time`)
        event_time (:obj:`float`): simulation time when the event must be executed (aka `receive_time`)
        sending_object (:obj:`~de_sim.simulation_object.SimulationObject`): reference to the object that sent the event
        receiving_object (:obj:`~de_sim.simulation_object.SimulationObject`): reference to the object that receives
            (aka executes) the event
        _order_time (:obj:`tuple`): the event time, sub-time that's used to sort events; cached
            to improve performance
        message (:obj:`~de_sim.event_message.EventMessage`): an :obj:`~de_sim.event_message.EventMessage` carried by
            the event; its type provides the simulation application's type for an :obj:`Event`; it may also carry a
            payload for the :obj:`Event` in its attribute(s) identified in its slots.
    """
    # TODO(Arthur): for performance, perhaps pre-allocate and reuse events

    # use __slots__ to save space
    # TODO(Arthur): figure out how to stop Sphinx from documenting these __slots__ as attributes
    __slots__ = "creation_time event_time sending_object receiving_object _order_time message".split()
    BASE_HEADERS = ['t(send)', 't(event)', 'Sender', 'Receiver', 'Event type']

    def __init__(self, creation_time, event_time, sending_object, receiving_object, message):
        self.creation_time = creation_time
        self.event_time = event_time
        self.sending_object = sending_object
        self.receiving_object = receiving_object
        # precompute _order_time to speed up simulation
        self._order_time = self._get_order_time()
        self.message = message

    def _get_order_time(self):
        """ Provide the tuple that determines this event's execution order

        Returns:
            :obj:`tuple`: the tuple that determines this event's execution order
        """
        return (self.event_time, self.receiving_object.class_event_priority,
                self.receiving_object.event_time_tiebreaker)

    def __lt__(self, other):
        """ Does this :obj:`Event` occur earlier than `other`?

        Args:
            other (:obj:`Event`): another :obj:`Event`

        Returns:
            :obj:`bool`: :obj:`True` if this :obj:`Event` occurs earlier than `other`
        """
        return self._order_time < other._order_time

    def __le__(self, other):
        """ Does this :obj:`Event` occur earlier or at the same time as `other`?

        Args:
            other (:obj:`Event`): another :obj:`Event`

        Returns:
            :obj:`bool`: `True` if this :obj:`Event` occurs earlier or at the same time as `other`
        """
        return not (other < self)

    def __gt__(self, other):
        """ Does this :obj:`Event` occur later than `other`?

        Args:
            other (:obj:`Event`): another :obj:`Event`

        Returns:
            :obj:`bool`: `True` if this :obj:`Event` occurs later than `other`
        """
        return self._order_time > other._order_time

    def __ge__(self, other):
        """ Does this :obj:`Event` occur later or at the same time as `other`?

        Args:
            other (:obj:`Event`): another :obj:`Event`

        Returns:
            :obj:`bool`: `True` if this :obj:`Event` occurs later or at the same time as `other`
        """
        return not (self < other)

    @staticmethod
    def header(as_list=False, separator='\t'):
        """ Provide a header row for an :obj:`Event` table

        Provide generic header suitable for any type of message in an event.

        Args:
            as_list (:obj:`bool`, optional): if set, return the header fields in a :obj:`list`
            separator (:obj:`str`, optional): the field separator used if the header is returned as
                a string

        Returns:
            :obj:`str` or obj:`str`: a string representation of names of an :obj:`Event`'s fields, or a :obj:`list`
            representation if `as_list` is set
        """
        MESSAGE_FIELDS_HEADER = 'Message fields...'
        list_repr = Event.BASE_HEADERS + [MESSAGE_FIELDS_HEADER]
        if as_list:
            return list_repr
        else:
            return separator.join(list_repr)

    def custom_header(self, as_list=False, separator='\t'):
        """ Return a header for an :obj:`Event` table containing messages of a particular type

        Args:
            as_list (:obj:`bool`, optional): if set, return the header fields in a :obj:`list`
            separator (:obj:`str`, optional): the field separator used if the header is returned as
                a string

        Returns:
            :obj:`str` or :obj:`list`: a string representation of the names of an :obj:`Event`'s fields,
            or a :obj:`list` representation if `as_list` is set
        """
        headers = list(Event.BASE_HEADERS)
        if self.message.header() is not None:
            headers.extend(self.message.header(as_list=True))
        if as_list:
            return headers
        else:
            return separator.join(headers)

    def render(self, round_w_direction=False, annotated=False, as_list=False, separator='\t'):
        """ Format the contents of an :obj:`Event`

        Rendering the contents assumes that `sending_object` and `receiving_object`
        have name attributes.

        Args:
            round_w_direction (:obj:`bool`, optional): if set, round times to strings indicating
                the direction of the rounding
            annotated (:obj:`bool`, optional): if set, prefix each message field value with its
                attribute name
            as_list (:obj:`bool`, optional): if set, return the :obj:`Event`'s values in a :obj:`list`
            separator (:obj:`str`, optional): the field separator used if the values are returned as
                a string

        Returns:
            :obj:`str` or :obj:`list`: string representation of the values of an :obj:`Event`'s fields,
            or a :obj:`list` representation if `as_list` is set
        """
        raw_times = [[self.creation_time], [self.event_time, str(self.receiving_object.class_event_priority),
                                            self.receiving_object.event_time_tiebreaker]]
        times = raw_times
        if round_w_direction:
            for t_list in raw_times:
                t_list[0] = round_direct(t_list[0])
            times = raw_times
        times = [tuple(t) for t in times]
        vals = times + [self.sending_object.name, self.receiving_object.name, self.message.__class__.__name__]
        if self.message.values():
            vals.extend(self.message.values(annotated=annotated, as_list=True))
        if as_list:
            return vals
        else:
            return separator.join(elements_to_str(vals))

    def __str__(self):
        """ Return an :obj:`Event` as a string

        Returns:
            :obj:`str`: String representation of the :obj:`Event`'s fields, except `message`,
            delimited by tabs
        """
        return self.render()
