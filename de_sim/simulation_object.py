""" Base class for simulation objects and their event queues

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-06-01
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

from abc import ABCMeta
from copy import deepcopy
from enum import IntEnum
import abc
import heapq
import math
import warnings

from de_sim.config import core
from de_sim.errors import SimulatorError
from de_sim.event import Event
from de_sim.simulation_message import SimulationMessage
from de_sim.utilities import ConcreteABCMeta, FastLogger
from wc_utils.util.list import elements_to_str
from wc_utils.util.misc import most_qual_cls_name, round_direct

config = core.get_config()


# TODO(Arthur): move to engine
class EventQueue(object):
    """ A simulation's event queue

    Stores a `SimulationEngine`'s events in a heap (also known as a priority queue).
    The heap is a 'min heap', which keeps the event with the smallest
    `(event_time, sending_object.name)` at the root in heap[0].
    This is implemented via comparison operations in `Event`.
    Thus, all entries with equal `(event_time, sending_object.name)` will be popped from the heap
    adjacently. `schedule_event()` costs `O(log(n))`, where `n` is the size of the heap,
    while `next_events()`, which returns all events with the minimum
    `(event_time, sending_object.name)`, costs `O(mlog(n))`, where `m` is the number of events
    returned.

    Attributes:
        event_heap (:obj:`list`): a `SimulationEngine`'s heap of events
        debug_logs (:obj:`wc_utils.debug_logs.core.DebugLogsManager`): a `DebugLogsManager`
    """

    def __init__(self):
        self.event_heap = []
        self.debug_logs = core.get_debug_logs()
        self.fast_debug_file_logger = FastLogger(self.debug_logs.get_log('de_sim.debug.file'), 'debug')

    def reset(self):
        self.event_heap = []

    def schedule_event(self, send_time, receive_time, sending_object, receiving_object, message):
        """ Create an event and insert in this event queue, scheduled to execute at `receive_time`

        Simulation object `X` can sends an event to simulation object `Y` by invoking
            `X.send_event(receive_delay, Y, message)`.

        Args:
            send_time (:obj:`float`): the simulation time at which the event was generated (sent)
            receive_time (:obj:`float`): the simulation time at which the `receiving_object` will
                execute the event
            sending_object (:obj:`SimulationObject`): the object sending the event
            receiving_object (:obj:`SimulationObject`): the object that will receive the event; when
                the simulation is parallelized `sending_object` and `receiving_object` will need
                to be global identifiers.
            message (:obj:`SimulationMessage`): a `SimulationMessage` carried by the event; its type
                provides the simulation application's type for an `Event`; it may also carry a payload
                for the `Event` in its attributes.

        Raises:
            :obj:`SimulatorError`: if `receive_time` < `send_time`, or `receive_time` or `send_time` is NaN
        """

        if math.isnan(send_time) or math.isnan(receive_time):
            raise SimulatorError("send_time ({}) and/or receive_time ({}) is NaN".format(
                receive_time, send_time))

        # Ensure that send_time <= receive_time.
        # Events with send_time == receive_time can cause loops, but the application programmer
        # is responsible for avoiding them.
        if receive_time < send_time:
            raise SimulatorError("receive_time < send_time in schedule_event(): {} < {}".format(
                receive_time, send_time))

        if not isinstance(message, SimulationMessage):
            raise SimulatorError("message should be an instance of {} but is a '{}'".format(
                SimulationMessage.__name__, type(message).__name__))

        event = Event(send_time, receive_time, sending_object, receiving_object, message)
        # As per David Jefferson's thinking, the event queue is ordered by data provided by the
        # simulation application, in particular the tuple (event time, receiving object name).
        # See the comparison operators for Event. This will achieve deterministic and reproducible
        # simulations.
        heapq.heappush(self.event_heap, event)

    def empty(self):
        """ Is the event queue empty?

        Returns:
            :obj:`bool`: return `True` if the event queue is empty
        """
        return not self.event_heap

    def next_event_time(self):
        """ Get the time of the next event

        Returns:
            :obj:`float`: the time of the next event; return infinity if no event is scheduled
        """
        if not self.event_heap:
            return float('inf')

        next_event = self.event_heap[0]
        next_event_time = next_event.event_time
        return next_event_time

    def next_event_obj(self):
        """ Get the simulation object that receives the next event

        Returns:
            :obj:`SimulationObject`): the simulation object that will execute the next event, or `None`
                if no event is scheduled
        """
        if not self.event_heap:
            return None

        next_event = self.event_heap[0]
        return next_event.receiving_object

    def next_events(self):
        """ Get all events at the smallest event time destined for the object whose name sorts earliest

        Because multiple events may occur concurrently -- that is, have the same simulation time --
        they must be provided as a collection to the simulation object that executes them.

        Handle 'ties' properly. That is, since an object may receive multiple events
        with the same event_time (aka receive_time), pass them all to the object in a list.

        Returns:
            :obj:`list` of :obj:`Event`: the earliest event(s), sorted by message type priority. If no
                events are available the list is empty.
        """
        if not self.event_heap:
            return []

        events = []
        next_event = heapq.heappop(self.event_heap)
        now = next_event.event_time
        receiving_obj = next_event.receiving_object
        events.append(next_event)

        # gather all events with the same event_time and receiving_object
        while (self.event_heap and now == self.next_event_time() and
               receiving_obj == self.next_event_obj()):
            events.append(heapq.heappop(self.event_heap))

        if 1 < len(events):
            # sort events by message type priority, and within priority by message content
            # thus, a sim object handles simultaneous messages in priority order;
            # this costs O(n log(n)) in the number of event messages in events
            receiver_priority_dict = receiving_obj.get_receiving_priorities_dict()
            events = sorted(events,
                            key=lambda event: (receiver_priority_dict[event.message.__class__], event.message))

        for event in events:
            self.log_event(event)

        return events

    def log_event(self, event):
        """ Log an event with its simulation time

        Args:
            event (:obj:`Event`): the Event to log
        """
        msg = "Execute: {} {}:{} {} ({})".format(event.event_time,
                                                 type(event.receiving_object).__name__,
                                                 event.receiving_object.name,
                                                 event.message.__class__.__name__,
                                                 str(event.message))
        self.fast_debug_file_logger.fast_log(msg, sim_time=event.event_time)

    def render(self, sim_obj=None, as_list=False, separator='\t'):
        """ Return the content of an `EventQueue`

        Make a human-readable event queue, sorted by non-decreasing event time.
        Provide a header row and a row for each event. If all events have the same type of message,
        the header contains event and message fields. Otherwise, the header has event fields and
        a message field label, and each event labels message fields with their attribute names.

        Args:
            sim_obj (:obj:`SimulationObject`, optional): if provided, return only events to be
                received by `sim_obj`
            as_list (:obj:`bool`, optional): if set, return the `EventQueue`'s values in a :obj:`list`
            separator (:obj:`str`, optional): the field separator used if the values are returned as
                a string

        Returns:
            :obj:`str`: String representation of the values of an `EventQueue`, or a :obj:`list`
                representation if `as_list` is set
        """
        event_heap = self.event_heap
        if sim_obj is not None:
            event_heap = list(filter(lambda event: event.receiving_object == sim_obj, event_heap))

        if not event_heap:
            return None

        # Sort the events in non-decreasing event time (receive_time, receiving_object.name)
        sorted_events = sorted(event_heap)

        # Does the queue contain multiple message types?
        message_types = set()
        for event in event_heap:
            message_types.add(event.message.__class__)
            if 1 < len(message_types):
                break
        multiple_msg_types = 1 < len(message_types)

        rendered_event_queue = []
        if multiple_msg_types:
            # The queue contains multiple message types
            rendered_event_queue.append(Event.header(as_list=True))
            for event in sorted_events:
                rendered_event_queue.append(event.render(annotated=True, as_list=True))

        else:
            # The queue contain only one message type
            # message_type = message_types.pop()
            event = sorted_events[0]
            rendered_event_queue.append(event.custom_header(as_list=True))
            for event in sorted_events:
                rendered_event_queue.append(event.render(as_list=True))

        if as_list:
            return rendered_event_queue
        else:
            table = []
            for row in rendered_event_queue:
                table.append(separator.join(elements_to_str(row)))
            return '\n'.join(table)

    def __str__(self):
        """ Return event queue members as a table
        """
        rv = self.render()
        if rv is None:
            return ''
        return rv


class SimulationObject(object):
    """ Base class for simulation objects.

    SimulationObject is a base class for all simulations objects. It provides basic functionality:
    the object's name (which must be unique), its simulation time, a queue of received events,
    and a send_event() method.

    Attributes:
        name (:obj:`str`): this simulation object's name, which is unique across all simulation objects
            handled by a `SimulationEngine`
        time (:obj:`float`): this simulation object's current simulation time
        event_time_tiebreaker (:obj:`str`): the least significant component of an object's 'sub-tme'
            priority, which orders simultaneous events received by different instances of the same
            `ApplicationSimulationObject`
        num_events (:obj:`int`): number of events processed
        simulator (:obj:`int`): the `SimulationEngine` that uses this `SimulationObject`
        debug_logs (:obj:`wc_utils.debug_logs.core.DebugLogsManager`): the debug logs
    """
    LOG_EVENTS = config['de_sim']['log_events']

    def __init__(self, name, start_time=0, **kwargs):
        """ Initialize a SimulationObject.

        Create its event queue, initialize its name, and set its start time.

        Args:
            name (:obj:`str`): the object's unique name, used as a key in the dict of objects
            start_time (:obj:`float`, optional): the earliest time at which this object can execute an event
            kwargs (:obj:`dict`): which can contain:
            event_time_tiebreaker (:obj:`str`, optional): used to break ties among simultaneous
                events; must be unique across all instances of an `ApplicationSimulationObject`
                class; defaults to `name`
        """
        self.name = name
        self.time = start_time
        self.num_events = 0
        self.simulator = None
        if 'event_time_tiebreaker' in kwargs and kwargs['event_time_tiebreaker']:
            self.event_time_tiebreaker = kwargs['event_time_tiebreaker']
        else:
            self.event_time_tiebreaker = name
        self.debug_logs = core.get_debug_logs()
        self.fast_debug_file_logger = FastLogger(self.debug_logs.get_log('de_sim.debug.file'), 'debug')
        self.fast_plot_file_logger = FastLogger(self.debug_logs.get_log('de_sim.plot.file'), 'debug')

    def add(self, simulator):
        """ Add this object to a simulation.

        Args:
            simulator (:obj:`SimulationEngine`): the simulator that will use this `SimulationObject`

        Raises:
            :obj:`SimulatorError`: if this `SimulationObject` is already registered with a simulator
        """
        if self.simulator is None:
            # TODO(Arthur): reference to the simulator is problematic because it means simulator can't be GC'ed
            self.simulator = simulator
            return
        raise SimulatorError("SimulationObject '{}' is already part of a simulator".format(self.name))

    def delete(self):
        """ Delete this object from a simulation.
        """
        # TODO(Arthur): is this an operation that makes sense to support? if not, remove it; if yes,
        # remove all of this object's state from simulator, and test it properly
        self.simulator = None

    def send_event_absolute(self, event_time, receiving_object, message, copy=False):
        """ Send a simulation event message with an absolute event time.

        Args:
            event_time (:obj:`float`): the absolute simulation time at which `receiving_object` will execute the event
            receiving_object (:obj:`SimulationObject`): the simulation object that will receive and
                execute the event
            message (:obj:`SimulationMessage`): the simulation message which will be carried by the event
            copy (:obj:`bool`, optional): if `True`, copy the message before adding it to the event;
                set `False` by default to optimize performance; set `True` as a safety measure to avoid
                unexpected changes to shared objects

        Raises:
            :obj:`SimulatorError`: if `event_time` < 0, or
                if the sending object type is not registered to send messages with the type of `message`, or
                if the receiving simulation object type is not registered to receive
                messages with the type of `message`
        """
        if math.isnan(event_time):
            raise SimulatorError("event_time is 'NaN'")
        if event_time < self.time:
            raise SimulatorError("event_time ({}) < current time ({}) in send_event_absolute()".format(
                round_direct(event_time, precision=3), round_direct(self.time, precision=3)))

        # Do not put a class reference in a message, as the message might not be received in the
        # same address space.
        # To eliminate the risk of name collisions use the fully qualified classname.
        # TODO(Arthur): wait until after MVP
        # event_type_name = most_qual_cls_name(message)
        event_type_name = message.__class__.__name__

        # check that the sending object type is registered to send the message type
        if not isinstance(message, SimulationMessage):
            raise SimulatorError("simulation messages must be instances of type 'SimulationMessage'; "
                                 "'{}' is not".format(event_type_name))
        if message.__class__ not in self.__class__.metadata.message_types_sent:
            raise SimulatorError("'{}' simulation objects not registered to send '{}' messages".format(
                most_qual_cls_name(self), event_type_name))

        # check that the receiving simulation object type is registered to receive the message type
        receiver_priorities = receiving_object.get_receiving_priorities_dict()
        if message.__class__ not in receiver_priorities:
            raise SimulatorError("'{}' simulation objects not registered to receive '{}' messages".format(
                most_qual_cls_name(receiving_object), event_type_name))

        if copy:
            message = deepcopy(message)

        self.simulator.event_queue.schedule_event(self.time, event_time, self,
                                                  receiving_object, message)
        self.log_with_time("Send: ({}, {:6.2f}) -> ({}, {:6.2f}): {}".format(self.name, self.time,
                                                                             receiving_object.name, event_time, message.__class__.__name__))

    def send_event(self, delay, receiving_object, message, copy=False):
        """ Send a simulation event message, specifing the event time as a delay.

        Args:
            delay (:obj:`float`): the simulation delay at which `receiving_object` should execute the event
            receiving_object (:obj:`SimulationObject`): the simulation object that will receive and
                execute the event
            message (:obj:`SimulationMessage`): the simulation message which will be carried by the event
            copy (:obj:`bool`, optional): if `True`, copy the message before adding it to the event;
                set `False` by default to optimize performance; set `True` as a safety measure to avoid
                unexpected changes to shared objects

        Raises:
            :obj:`SimulatorError`: if `delay` < 0 or `delay` is NaN, or
                if the sending object type is not registered to send messages with the type of `message`, or
                if the receiving simulation object type is not registered to receive messages with
                the type of `message`
        """
        if math.isnan(delay):
            raise SimulatorError("delay is 'NaN'")
        if delay < 0:
            raise SimulatorError("delay < 0 in send_event(): {}".format(str(delay)))
        self.send_event_absolute(delay + self.time, receiving_object, message, copy=copy)

    @staticmethod
    def register_handlers(subclass, handlers):
        """ Register a `SimulationObject`'s event handler methods.

        The simulation engine vectors execution of a simulation message to the message's registered
        event handler method. The priority of message execution in an event containing multiple messages
        is determined by the sequence of tuples in `handlers`.
        These relationships are stored in an `ApplicationSimulationObject`'s
        `metadata.event_handlers_dict`.
        Each call to `register_handlers` re-initializes all event handler methods.

        Args:
            subclass (:obj:`SimulationObject`): a subclass of `SimulationObject` that is registering
                the relationships between the simulation messages it receives and the methods that
                handle them
            handlers (:obj:`list` of (`SimulationMessage`, `function`)): a list of tuples, indicating
                which method should handle which type of `SimulationMessage` in `subclass`; ordered in
                decreasing priority for handling simulation message types

        Raises:
            :obj:`SimulatorError`: if a `SimulationMessage` appears repeatedly in `handlers`, or
                if a method in `handlers` is not callable
        """
        for message_type, handler in handlers:
            if message_type in subclass.metadata.event_handlers_dict:
                raise SimulatorError("message type '{}' appears repeatedly".format(
                    most_qual_cls_name(message_type)))
            if not callable(handler):
                raise SimulatorError("handler '{}' must be callable".format(handler))
            subclass.metadata.event_handlers_dict[message_type] = handler

        for index, (message_type, _) in enumerate(handlers):
            subclass.metadata.event_handler_priorities[message_type] = index

    @staticmethod
    def register_sent_messages(subclass, sent_messages):
        """ Register the messages sent by a `SimulationObject` subclass

        Calling `register_sent_messages` re-initializes all registered sent message types.

        Args:
            subclass (:obj:`SimulationObject`): a subclass of `SimulationObject` that is registering
                the types of simulation messages it sends
            sent_messages (:obj:`list` of :obj:`SimulationMessage`): a list of the `SimulationMessage`
                type's which can be sent by `SimulationObject`'s of type `subclass`
        """
        for sent_message_type in sent_messages:
            subclass.metadata.message_types_sent.add(sent_message_type)

    def get_receiving_priorities_dict(self):
        """ Get priorities of message types handled by this `SimulationObject`'s type

        Returns:
            :obj:`dict`: mapping from message types handled by this `SimulationObject` to their
                execution priorities. The highest priority is 0, and higher values have lower
                priorities. Execution priorities determine the execution order of concurrent events
                at a `SimulationObject`.
        """
        return self.__class__.metadata.event_handler_priorities

    def _SimulationEngine__handle_event_list(self, event_list):
        """ Handle a list of simulation events, which may contain multiple concurrent events

        This method's special name ensures that it cannot be overridden, and can only be called
        from `SimulationEngine`.

        Attributes:
            event_list (:obj:`list` of :obj:`Event`): the `Event` message(s) in the simulation event

        Raises:
            :obj:`SimulatorError`: if a message in `event_list` has an invalid type
        """
        self.num_events += 1

        if self.LOG_EVENTS:
            # write events to a plot log
            # plot logging is controlled by configuration files pointed to by config_constants and by env vars
            for event in event_list:
                self.fast_plot_file_logger.fast_log(str(event), sim_time=self.time)

        # iterate through event_list, branching to handler
        for event in event_list:
            try:
                handler = self.__class__.metadata.event_handlers_dict[event.message.__class__]
                handler(self, event)
            except KeyError:  # pragma: no cover
                # unreachable because of check that receiving sim
                # obj type is registered to receive the message type
                raise SimulatorError("No handler registered for Simulation message type: '{}'".format(
                    event.message.__class__.__name__))

    @property
    def class_event_priority(self):
        """ Get the event priority of this simulation object's class

        Returns:
            :obj:`int`: the event priority of this simulation object's class
        """
        return self.__class__.metadata.class_priority

    def render_event_queue(self):
        """ Format an event queue as a string

        Returns:
            :obj:`str`: return a string representation of the simulator's event queue
        """
        return self.simulator.event_queue.render()

    def log_with_time(self, msg):
        """ Write a debug log message with the simulation time.
        """
        self.fast_debug_file_logger.fast_log(msg, sim_time=self.time)


class ApplicationSimulationObjectInterface(object, metaclass=ABCMeta):  # pragma: no cover

    @abc.abstractmethod
    def send_initial_events(self, *args):
        pass

    @abc.abstractmethod
    def get_state(self):
        pass


class SimObjClassPriority(IntEnum):
    """ Simultaneous execution priority for simulation object classes, used in `class_priority`
    """
    HIGH = 1
    MEDIUM = 5
    LOW = 9
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4
    FIFTH = 5
    SIXTH = 6
    SEVENTH = 7
    EIGHTH = 8
    NINTH = 9

    @classmethod
    def assign_decreasing_priority(cls, aso_classes):
        """ Assign decreasing simultaneous execution priorities for a list of simulation object classes

        Args:
            aso_classes (:obj:`iterator` of :obj:`ApplicationSimulationObject`): an iterator over
                simulation object classes

        Raises:
            :obj:`SimulatorError`: if too many :obj:`ApplicationSimulationObject`\ s are given
        """
        if cls.LOW < len(aso_classes):
            raise SimulatorError(f"Too many ApplicationSimulationObjects: {len(aso_classes)}")
        for index, aso_class in enumerate(aso_classes):
            aso_class.set_class_priority(SimObjClassPriority(index + 1))

    def __str__(self):
        return f'{self.name}: {self.value}'


class ApplicationSimulationObjectMetadata(object):
    """ Metadata for an :class:`ApplicationSimulationObject`

    Attributes:
        event_handlers_dict (:obj:`dict`): maps message_type -> event_handler; provides the event
            handler for each message type for a subclass of `SimulationObject`
        event_handler_priorities (:obj:`dict`): maps message_type -> message_type priority; the highest
            priority is 0, and priority decreases with increasing priority values.
        message_types_sent (:obj:`set`): the types of messages a subclass of `SimulationObject` has
            registered to send
    """

    def __init__(self):
        self.event_handlers_dict = {}
        self.event_handler_priorities = {}
        self.message_types_sent = set()
        self.class_priority = SimObjClassPriority.LOW


class ApplicationSimulationObjMeta(type):
    # event handler mapping keyword
    EVENT_HANDLERS = 'event_handlers'
    # messages sent list keyword
    MESSAGES_SENT = 'messages_sent'
    # keyword for a class' 'subtime' priority, used to order concurrent events among classes
    CLASS_PRIORITY = 'class_priority'

    def __new__(cls, clsname, superclasses, namespace):
        """
        Args:
            cls (:obj:`class`): this class
            clsname (:obj:`str`): name of the :class:`SimulationObject` subclass being created
            superclasses (:obj:`tuple`): tuple of superclasses
            namespace (:obj:`dict`): namespace of subclass of `ApplicationSimulationObject` being created

        Returns:
            :obj:`SimulationObject`: a new instance of a subclass of `SimulationObject`

        Raises:
            :obj:`SimulatorError`: if class priority is not an `int`,
                or if the :obj:`ApplicationSimulationObject` doesn't define `messages_sent` or `event_handlers`,
                or if handlers in `event_handlers` don't refer to methods in the
                    :obj:`ApplicationSimulationObject`,
                or if `event_handlers` isn't an iterator over pairs,
                or if a message type sent isn't a subclass of SimulationMessage,
                or if `messages_sent` isn't an iterator over pairs.
        """
        # Short circuit when ApplicationSimulationObject is defined
        if clsname == 'ApplicationSimulationObject':
            return super().__new__(cls, clsname, superclasses, namespace)

        EVENT_HANDLERS = cls.EVENT_HANDLERS
        MESSAGES_SENT = cls.MESSAGES_SENT
        CLASS_PRIORITY = cls.CLASS_PRIORITY

        new_application_simulation_obj_subclass = super().__new__(cls, clsname, superclasses, namespace)
        new_application_simulation_obj_subclass.metadata = ApplicationSimulationObjectMetadata()

        # use 'abstract' to indicate that an ApplicationSimulationObject should not be instantiated
        if 'abstract' in namespace and namespace['abstract'] is True:
            return new_application_simulation_obj_subclass

        # approach:
        #     look for EVENT_HANDLERS & MESSAGES_SENT attributes:
        #         use declaration in namespace, if found
        #         use first definition in metadata of a superclass, if found
        #         if not found, issue warning and return or raise exception
        #
        #     found:
        #         if EVENT_HANDLERS found, check types, and use register_handlers() to set
        #         if MESSAGES_SENT found, check types, and use register_sent_messages() to set

        event_handlers = None
        if EVENT_HANDLERS in namespace:
            event_handlers = namespace[EVENT_HANDLERS]

        messages_sent = None
        if MESSAGES_SENT in namespace:
            messages_sent = namespace[MESSAGES_SENT]

        class_priority = None
        if CLASS_PRIORITY in namespace:
            class_priority = namespace[CLASS_PRIORITY]
            if not isinstance(class_priority, int):
                raise SimulatorError(f"ApplicationSimulationObject '{clsname}' {CLASS_PRIORITY} must be "
                                     f"an int, but '{class_priority}' is a {type(class_priority).__name__}")

        for superclass in superclasses:
            if event_handlers is None:
                if hasattr(superclass, 'metadata') and hasattr(superclass.metadata, 'event_handlers_dict'):
                    # convert dict in superclass to list of tuple pairs
                    event_handlers = [(k, v) for k, v in getattr(superclass.metadata,
                                                                 'event_handlers_dict').items()]

        for superclass in superclasses:
            if messages_sent is None:
                if hasattr(superclass, 'metadata') and hasattr(superclass.metadata, 'message_types_sent'):
                    messages_sent = getattr(superclass.metadata, 'message_types_sent')

        for superclass in superclasses:
            if class_priority is None:
                if hasattr(superclass, 'metadata') and hasattr(superclass.metadata, CLASS_PRIORITY):
                    class_priority = getattr(superclass.metadata, CLASS_PRIORITY)
        if class_priority is not None:
            setattr(new_application_simulation_obj_subclass.metadata, CLASS_PRIORITY, class_priority)

        # either messages_sent or event_handlers must contain values
        if (not event_handlers and not messages_sent):
            raise SimulatorError("ApplicationSimulationObject '{}' definition must inherit or provide a "
                                 "non-empty '{}' or '{}'.".format(clsname, EVENT_HANDLERS, MESSAGES_SENT))
        elif not event_handlers:
            warnings.warn("ApplicationSimulationObject '{}' definition does not inherit or provide a "
                          "non-empty '{}'.".format(clsname, EVENT_HANDLERS))
        elif not messages_sent:
            warnings.warn("ApplicationSimulationObject '{}' definition does not inherit or provide a "
                          "non-empty '{}'.".format(clsname, MESSAGES_SENT))

        if event_handlers:
            try:
                resolved_handers = []
                errors = []
                for msg_type, handler in event_handlers:
                    # handler may be the string name of a method
                    if isinstance(handler, str):
                        try:
                            handler = namespace[handler]
                        except Exception:
                            errors.append("ApplicationSimulationObject '{}' definition must define "
                                          "'{}'.".format(clsname, handler))
                    if not isinstance(handler, str) and not callable(handler):
                        errors.append("handler '{}' must be callable".format(handler))
                    if not issubclass(msg_type, SimulationMessage):
                        errors.append("'{}' must be a subclass of SimulationMessage".format(msg_type.__name__))
                    resolved_handers.append((msg_type, handler))

                if errors:
                    raise SimulatorError("\n".join(errors))
                new_application_simulation_obj_subclass.register_handlers(
                    new_application_simulation_obj_subclass, resolved_handers)
            except (TypeError, ValueError):
                raise SimulatorError("ApplicationSimulationObject '{}': '{}' must iterate over pairs".format(
                    clsname, EVENT_HANDLERS))

        if messages_sent:
            try:
                errors = []
                for msg_type in messages_sent:
                    if not issubclass(msg_type, SimulationMessage):
                        errors.append("'{}' in '{}' must be a subclass of SimulationMessage".format(
                            msg_type.__name__, MESSAGES_SENT))
                if errors:
                    raise SimulatorError("\n".join(errors))
                new_application_simulation_obj_subclass.register_sent_messages(
                    new_application_simulation_obj_subclass, messages_sent)
            except (TypeError, ValueError):
                raise SimulatorError("ApplicationSimulationObject '{}': '{}' must iterate over "
                                     "SimulationMessages".format(clsname, MESSAGES_SENT))

        # return the class to instantiate it
        return new_application_simulation_obj_subclass


class AppSimObjAndABCMeta(ApplicationSimulationObjMeta, ConcreteABCMeta):
    """ A concrete class based on two Meta classes to be used as a metaclass for classes derived from both
    """
    pass


class ApplicationSimulationObject(SimulationObject, ApplicationSimulationObjectInterface,
                                  metaclass=AppSimObjAndABCMeta):
    """ Base class for all simulation objects in a simulation

    Attributes:
        metadata (:obj:`ApplicationSimulationObjectMetadata`): metadata for event message sending and handling,
            initialized by `AppSimObjAndABCMeta`
    """

    def send_initial_events(self, *args):
        pass  # pragma: no cover

    def get_state(self):
        pass  # pragma: no cover

    @classmethod
    def set_class_priority(cls, priority):
        """ Set the execution priority for simulation object classes, `class_priority`

        Use this to set the `class_priority` of a subclass of :obj:`SimulationObject` after it
            has been constructed.

        Args:
            priority (:obj:`SimObjClassPriority`): the desired `class_priority` for a subclass
                of :obj:`SimulationObject`
        """
        setattr(cls.metadata, ApplicationSimulationObjMeta.CLASS_PRIORITY, priority)
