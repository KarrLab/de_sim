""" Simulation event structure

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-05-31
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

from collections.abc import Iterable

from wc_utils.util.misc import round_direct
from wc_utils.util.list import elements_to_str
from de_sim.simulation_message import SimulationMessage  # noqa: F401


class Event(object):
    """ An object that holds a discrete event simulation (DES) event

    Each DES event is scheduled by creating an `Event` instance and storing it in the
    simulator's event queue. To reduce interface errors the `message`
    attribute must be structured as specified in the `message_types` module.

    As per David Jefferson's thinking, the event queue is ordered by data provided by the
    simulation application, in particular (event time, sub-time), where 'sub-time' determines the
    execution priority among simultaneous messages with the same event time at different simulation
    objects.
    This is implemented by the comparison operators for Event below. This ordering achieves
    deterministic and reproducible simulations. (See Jefferson's LLNL course.)

    Attributes:
        creation_time (:obj:`float`): simulation time when the event is created (aka `send_time`)
        event_time (:obj:`float`): simulation time when the event must be executed (aka `receive_time`)
        sending_object (:obj:`SimulationObject`): reference to the object that sends the event
        receiving_object (:obj:`SimulationObject`): reference to the object that receives
            (aka executes) the event
        _order_time (:obj:`tuple`): the event time, sub-time that's used to sort events; cached
            to improve performance
        message (:obj:`SimulationMessage`): a :obj:`SimulationMessage` carried by the event; its type
            provides the simulation application's type for an `Event`; it may also carry a payload
            for the `Event` in its attributes.
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
        self._order_time = self._get_order_time()
        self.message = message

    def _get_order_time(self):
        """ Provide the tuple that determines this event's time order

        Returns:
            :obj:`tuple`: the tuple that determines this event's time order
        """
        return (self.event_time, self.receiving_object.class_event_priority,
                self.receiving_object.event_time_tiebreaker)

    def __lt__(self, other):
        """ Does this `Event` occur earlier than `other`?

        Args:
            other (:obj:`Event`): another `Event`

        Returns:
            :obj:`bool`: `True` if this `Event` occurs earlier than `other`
        """
        return self._order_time < other._order_time

    def __le__(self, other):
        """ Does this `Event` occur earlier or at the same time as `other`?

        Args:
            other (:obj:`Event`): another `Event`

        Returns:
            :obj:`bool`: `True` if this `Event` occurs earlier or at the same time as `other`
        """
        return not (other < self)

    def __gt__(self, other):
        """ Does this `Event` occur later than `other`?

        Args:
            other (:obj:`Event`): another `Event`

        Returns:
            :obj:`bool`: `True` if this `Event` occurs later than `other`
        """
        return self._order_time > other._order_time

    def __ge__(self, other):
        """ Does this `Event` occur later or at the same time as `other`?

        Args:
            other (:obj:`Event`): another `Event`

        Returns:
            :obj:`bool`: `True` if this `Event` occurs later or at the same time as `other`
        """
        return not (self < other)

    @staticmethod
    def header(as_list=False, separator='\t'):
        """ Return a header for an :obj:`Event` table

        Provide generic header suitable for any type of message in an event.

        Args:
            as_list (:obj:`bool`, optional): if set, return the header fields in a :obj:`list`
            separator (:obj:`str`, optional): the field separator used if the header is returned as
                a string

        Returns:
            :obj:`str`: String representation of names of an :obj:`Event`'s fields, or a :obj:`list`
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
            :obj:`str`: String representation of names of an `Event`'s fields, or a :obj:`list`
                representation if `as_list` is set
        """
        headers = list(Event.BASE_HEADERS)
        if self.message.header() is not None:
            headers.extend(self.message.header(as_list=True))
        if as_list:
            return headers
        else:
            return separator.join(headers)

    def render(self, round_w_direction=False, annotated=False, as_list=False, separator='\t'):
        """ Format the content of an `Event`

        Rendering the content assumes that `sending_object` and `receiving_object`
        have name attributes.

        Args:
            round_w_direction (:obj:`bool`, optional): if set, round times to strings indicating
                the direction of the rounding
            annotated (:obj:`bool`, optional): if set, prefix each message field value with its
                attribute name
            as_list (:obj:`bool`, optional): if set, return the `Event`'s values in a :obj:`list`
            separator (:obj:`str`, optional): the field separator used if the values are returned as
                a string

        Returns:
            :obj:`str`: String representation of the values of an `Event`'s fields, or a :obj:`list`
                representation if `as_list` is set
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
        """ Return an `Event` as a string

        Returns:
            :obj:`str`: String representation of the `Event`'s fields, except `message`,
                delimited by tabs
        """
        return self.render()


def iterable_not_str(obj):
    """ Is an object an iterable, but not a string?

    Args:
        obj (:obj:`object`): an object

    Returns:
        :obj:`bool`: `True` if `obj` is an iterable, but not a string
    """
    return isinstance(obj, Iterable) and not isinstance(obj, str)


def nested_elements_to_str(o):
    """ Obtain `str()` values of all elements of o, recursively, while retaining the same structure

    Args:
        o (:obj:`obj`): an object

    Returns:
        :obj:`obj`: stringified instance of `o`
    """
    if iterable_not_str(o):
        return [nested_elements_to_str(e) for e in o]
    return str(o)
