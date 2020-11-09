""" Base class for simulation objects

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-06-01
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

from abc import ABCMeta
from copy import deepcopy
from enum import IntEnum
import abc
import math
import warnings

from de_sim.config import core
from de_sim.errors import SimulatorError
from de_sim.event_message import EventMessage
from de_sim.utilities import ConcreteABCMeta, FastLogger
from wc_utils.util.misc import most_qual_cls_name, round_direct
import de_sim  # noqa: F401


class BaseSimulationObject(object):
    """ Base class for simulation objects.

    :class:`BaseSimulationObject` is a base class for all simulations objects. It provides basic functionality
    which includes
    the object's `name` (which must be unique), its simulation time, and a `send_event()` method.

    Attributes:
        name (:obj:`str`): this simulation object's name, which must be unique across all simulation objects
            handled by a :obj:`~de_sim.simulator.Simulator`
        time (:obj:`float`): this simulation object's current simulation time
        event_time_tiebreaker (:obj:`str`): the least significant component of an object's 'sub-tme'
            priority, which orders simultaneous events received by different instances of the same
            :obj:`SimulationObject` class
        num_events (:obj:`int`): number of events processed
        simulator (:obj:`~de_sim.simulator.Simulator`): the :obj:`~de_sim.simulator.Simulator` that uses
            this :class:`BaseSimulationObject`
        debug_logs (:obj:`wc_utils.debug_logs.core.DebugLogsManager`): the debug logs
    """

    def __init__(self, name, start_time=0, **kwargs):
        """ Initialize a :class:`BaseSimulationObject`.

        Args:
            name (:obj:`str`): the object's unique name, used as a key in the dict of objects
            start_time (:obj:`float`, optional): the earliest time at which this object can execute an event
            kwargs (:obj:`dict`): which can contain:
            event_time_tiebreaker (:obj:`str`, optional): used to break ties among simultaneous
                events; must be unique across all instances of a :obj:`SimulationObject`
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
        config = core.get_config()
        self.log_events = config['de_sim']['log_events']
        self.debug_logs = core.get_debug_logs()
        self.fast_debug_file_logger = FastLogger(self.debug_logs.get_log('de_sim.debug.file'), 'debug')
        self.fast_plot_file_logger = FastLogger(self.debug_logs.get_log('de_sim.plot.file'), 'debug')

    def set_simulator(self, simulator):
        """ Set this object's simulator reference

        Args:
            simulator (:obj:`~de_sim.simulator.Simulator`): the simulator that will use
                this :obj:`BaseSimulationObject`

        Raises:
            :obj:`SimulatorError`: if this :obj:`BaseSimulationObject` is already registered with a simulator
        """
        if self.simulator is None:
            self.simulator = simulator
            return
        raise SimulatorError("SimulationObject '{}' is already part of a simulator".format(self.name))

    def del_simulator(self):
        """ Delete this object's simulator reference
        """
        self.simulator = None

    def send_event_absolute(self, event_time, receiving_object, message, copy=False):
        """ Schedule an event containing an event message with an absolute event time.

        Args:
            event_time (:obj:`float`): the absolute simulation time at which `receiving_object` will execute the event
            receiving_object (:obj:`SimulationObject`): the simulation object that will receive and
                execute the event
            message (:obj:`~de_sim.event_message.EventMessage`): the event message which will be carried by the event
            copy (:obj:`bool`, optional): if :obj:`True`, copy the message before adding it to the event;
                set :obj:`False` by default to optimize performance; set :obj:`True` as a safety measure to avoid
                unexpected changes to shared objects

        Raises:
            :obj:`SimulatorError`: if `event_time < 0`, or
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
        # To eliminate the risk of name collisions use the fully qualified class name.
        # TODO(Arthur): wait until after MVP
        # event_type_name = most_qual_cls_name(message)
        event_type_name = message.__class__.__name__

        # check that the sending object type is registered to send the message type
        if not isinstance(message, EventMessage):
            raise SimulatorError("event messages must be instances of type 'EventMessage'; "
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
                                                                             receiving_object.name, event_time,
                                                                             message.__class__.__name__))

    def send_event(self, delay, receiving_object, event_message, copy=False):
        """ Schedule an event containing an event message, specifying the event time as a delay.

        Simulation object `X` sends an event to simulation object `Y` by invoking

            X.send_event(receive_delay, Y, event_message)

        Args:
            delay (:obj:`float`): the simulation delay at which `receiving_object` should execute the event
            receiving_object (:obj:`SimulationObject`): the simulation object that will receive and
                execute the event
            event_message (:obj:`~de_sim.event_message.EventMessage`): the event message which will be
                carried by the event
            copy (:obj:`bool`, optional): if :obj:`True`, copy the message before adding it to the event;
                set :obj:`False` by default to optimize performance; set :obj:`True` as a safety measure to avoid
                unexpected changes to shared objects

        Raises:
            :obj:`SimulatorError`: if `delay` < 0 or `delay` is NaN, or
                if the sending object type is not registered to send messages with the type of `event_message`, or
                if the receiving simulation object type is not registered to receive messages with
                the type of `event_message`
        """
        if math.isnan(delay):
            raise SimulatorError("delay is 'NaN'")
        if delay < 0:
            raise SimulatorError("delay < 0 in send_event(): {}".format(str(delay)))
        self.send_event_absolute(delay + self.time, receiving_object, event_message, copy=copy)

    @staticmethod
    def register_handlers(subclass, handlers):
        """ Register a :class:`BaseSimulationObject`'s event handler methods.

        The simulator vectors execution of an event message to the message's registered
        event handler method. The priority of message execution in an event containing multiple messages
        is determined by the sequence of tuples in `handlers`.
        These relationships are stored in a :obj:`SimulationObject`'s
        `metadata.event_handlers_dict`.
        Each call to `register_handlers` reinitializes all event handler methods.

        Args:
            subclass (:class:`BaseSimulationObject`): a subclass of :class:`BaseSimulationObject` that is registering
                the relationships between the event messages it receives and the methods that
                handle them
            handlers (:obj:`list` of (:obj:`~de_sim.event_message.EventMessage`, `method`)): a list of tuples,
                indicating which method should handle which type of :class:`~de_sim.event_message.EventMessage`
                in `subclass`; ordered in decreasing priority for handling event message types

        Raises:
            :obj:`SimulatorError`: if an :obj:`~de_sim.event_message.EventMessage` appears repeatedly in `handlers`, or
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
        """ Register the messages sent by a :class:`BaseSimulationObject` subclass

        Calling `register_sent_messages` reinitializes all registered sent message types.

        Args:
            subclass (:class:`BaseSimulationObject`): a subclass of :class:`BaseSimulationObject` that is registering
                the types of event messages it sends
            sent_messages (:obj:`list` of :obj:`~de_sim.event_message.EventMessage`): a list of the
                :class:`~de_sim.event_message.EventMessage` classes which can be sent by
                :class:`BaseSimulationObject`'s of type `subclass`
        """
        for sent_message_type in sent_messages:
            subclass.metadata.message_types_sent.add(sent_message_type)

    def get_receiving_priorities_dict(self):
        """ Get priorities of message types handled by this :obj:`SimulationObject`'s type

        Returns:
            :obj:`dict`: mapping from message types handled by this :obj:`SimulationObject` to their
            execution priorities. The highest priority is 0, and higher values have lower
            priorities. Execution priorities determine the execution order of concurrent events
            at a :obj:`SimulationObject`.
        """
        return self.__class__.metadata.event_handler_priorities

    def __handle_event_list(self, event_list):
        """ Handle a list of simulation events, which may contain multiple concurrent events

        This is a Python 'dunder' method which creates a class-private member,
        reducing the chance that it will be accidentally called or overwritten.
        :obj:`~de_sim.simulator.Simulator` refers to this method via `sim_obj._BaseSimulationObject__handle_event_list`,
        where `sim_obj` is the simulation object that receives the event list.

        If multiple event messages are received by a simulation object at the same simulation time,
        then they are all passed in a list to the simulation object's handler.
        This functionality, named *superposition* after the concept in physics, is important because
        simulations must be deterministic, and to achieve that the simulation application must receive
        all simultanous messages at once and execute them in a deterministically.
        The alternative, in which the simulator passes simultaneous event messages in an arbitrary
        order to a simulation object would **not** give the object sufficient information to be deterministic.
        But if the event messages have different handlers then the simulator raises a
        :obj:`~de_sim.errors.SimulatorError` exception which says that superposition requires that the message types
        have the same handler.

        Attributes:
            event_list (:obj:`list` of :obj:`~de_sim.event.Event`): the :obj:`~de_sim.event.Event`
                message(s) in the simulation event

        Raises:
            :obj:`SimulatorError`: if a message in `event_list` has an invalid type, or
            if superposed event messages have different handlers
        """
        self.num_events += len(event_list)

        if self.log_events: # cannot be conveniently unit-tested because doing so requires that config state be changed
                            # before de_sim.plot.file logger is created
                            # therefore, is tested by tests/joss_paper/test_gen_phold_space_time_plot.py
            # write events to a plot log
            # plot logging is controlled by configuration files pointed to by config_constants and by env vars
            for event in event_list:
                self.fast_plot_file_logger.fast_log(str(event), sim_time=self.time)

        # if only one event message is being handled, call its handler
        if 1 == len(event_list):
            event = event_list[0]
            try:
                handler = self.__class__.metadata.event_handlers_dict[event.message.__class__]
                handler(self, event)
            except KeyError:  # pragma: no cover
                # unreachable because of check that receiving sim
                # obj type is registered to receive the message type
                raise SimulatorError("No handler registered for event message type: '{}'".format(
                    event.message.__class__.__name__))

        # if multiple event messages are being handled, pass them as a list to an event handler,
        # which is known as "superposition"
        else:
            try:
                handler = self.__class__.metadata.event_handlers_dict[event_list[0].message.__class__]
                for event in event_list[1:]:
                    if handler != self.__class__.metadata.event_handlers_dict[event.message.__class__]:
                        message_types = set([type(event.message).__name__ for event in event_list])
                        raise SimulatorError(f"Superposition requires message types {message_types} have same handler")
                handler(self, event_list)
            except KeyError:  # pragma: no cover
                # unreachable because of check that receiving sim obj type is registered to receive the message type
                raise SimulatorError("No handler registered for event message type: '{}'".format(
                    event.message.__class__.__name__))

    @property
    def class_event_priority(self):
        """ Get the event priority of this simulation object's class

        Returns:
            :obj:`int`: the event priority of this simulation object's class
        """
        return self.__class__.metadata.class_priority

    def log_with_time(self, msg):
        """ Write a debug log message with the simulation time.
        """
        self.fast_debug_file_logger.fast_log(msg, sim_time=self.time)


class SimulationObjectInterface(object, metaclass=ABCMeta):  # pragma: no cover

    @abc.abstractmethod
    def init_before_run(self):
        """ Perform initialization before a simulation run """
        pass


class SimObjClassPriority(IntEnum):
    """ Priorities for simulation object classes

    These are used to order the execution of simultaneous events among objects in different classes
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
    def assign_decreasing_priority(cls, so_classes):
        """ Assign decreasing simultaneous execution priorities for a list of simulation object classes

        Args:
            so_classes (:obj:`iterator` of :obj:`SimulationObject`): an iterator over
                simulation object classes

        Raises:
            :obj:`SimulatorError`: if too many :obj:`SimulationObject`\ s are given
        """
        if cls.LOW < len(so_classes):
            raise SimulatorError(f"Too many SimulationObjects: {len(so_classes)}")
        for index, so_class in enumerate(so_classes):
            so_class.set_class_priority(SimObjClassPriority(index + 1))

    def __str__(self):
        return f'{self.name}: {self.value}'


class SimulationObjectMetadata(object):
    """ Metadata for a :class:`SimulationObject`

    Attributes:
        event_handlers_dict (:obj:`dict`): maps message_type -> event_handler; provides the event
            handler for each message type for a subclass of :class:`BaseSimulationObject`
        event_handler_priorities (:obj:`dict`): maps message_type -> message_type priority; the highest
            priority is 0, and priority decreases with increasing priority values.
        message_types_sent (:obj:`set`): the types of messages a subclass of :class:`BaseSimulationObject` has
            registered to send
    """

    def __init__(self):
        self.event_handlers_dict = {}
        self.event_handler_priorities = {}
        self.message_types_sent = set()
        self.class_priority = SimObjClassPriority.LOW


class SimulationObjMeta(type):
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
            clsname (:obj:`str`): name of the :class:`BaseSimulationObject` subclass being created
            superclasses (:obj:`tuple`): tuple of superclasses
            namespace (:obj:`dict`): namespace of subclass of :obj:`SimulationObject` being created

        Returns:
            :obj:`SimulationObject`: a new instance of a subclass of :class:`BaseSimulationObject`

        Raises:
            :obj:`SimulatorError`: if class priority is not an `int`,
                or if the :obj:`SimulationObject` doesn't define `messages_sent` or `event_handlers`,
                or if handlers in `event_handlers` don't refer to methods in the
                    :obj:`SimulationObject`,
                or if `event_handlers` isn't an iterator over pairs,
                or if a message type sent isn't a subclass of :obj:`~de_sim.event_message.EventMessage`,
                or if `messages_sent` isn't an iterator over pairs.
        """
        # Short circuit when SimulationObject is defined
        if clsname == 'SimulationObject':
            return super().__new__(cls, clsname, superclasses, namespace)

        EVENT_HANDLERS = cls.EVENT_HANDLERS
        MESSAGES_SENT = cls.MESSAGES_SENT
        CLASS_PRIORITY = cls.CLASS_PRIORITY

        new_application_simulation_obj_subclass = super().__new__(cls, clsname, superclasses, namespace)
        new_application_simulation_obj_subclass.metadata = SimulationObjectMetadata()

        # use 'abstract' to indicate that an SimulationObject should not be instantiated
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
                raise SimulatorError(f"SimulationObject '{clsname}' {CLASS_PRIORITY} must be "
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
            raise SimulatorError("SimulationObject '{}' definition must inherit or provide a "
                                 "non-empty '{}' or '{}'.".format(clsname, EVENT_HANDLERS, MESSAGES_SENT))
        elif not event_handlers:
            warnings.warn("SimulationObject '{}' definition does not inherit or provide a "
                          "non-empty '{}'.".format(clsname, EVENT_HANDLERS))

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
                            errors.append("SimulationObject '{}' definition must define "
                                          "'{}'.".format(clsname, handler))
                    if not isinstance(handler, str) and not callable(handler):
                        errors.append("handler '{}' must be callable".format(handler))
                    if not issubclass(msg_type, EventMessage):
                        errors.append("'{}' must be a subclass of EventMessage".format(msg_type.__name__))
                    resolved_handers.append((msg_type, handler))

                if errors:
                    raise SimulatorError("\n".join(errors))
                new_application_simulation_obj_subclass.register_handlers(
                    new_application_simulation_obj_subclass, resolved_handers)
            except (TypeError, ValueError):
                raise SimulatorError("SimulationObject '{}': '{}' must iterate over pairs".format(
                    clsname, EVENT_HANDLERS))

        if messages_sent:
            try:
                errors = []
                for msg_type in messages_sent:
                    if not issubclass(msg_type, EventMessage):
                        errors.append("'{}' in '{}' must be a subclass of EventMessage".format(
                                      msg_type.__name__, MESSAGES_SENT))
                if errors:
                    raise SimulatorError("\n".join(errors))
                new_application_simulation_obj_subclass.register_sent_messages(
                    new_application_simulation_obj_subclass, messages_sent)
            except (TypeError, ValueError):
                raise SimulatorError("SimulationObject '{}': '{}' must iterate over "
                                     "EventMessages".format(clsname, MESSAGES_SENT))

        # return the class to instantiate it
        return new_application_simulation_obj_subclass


class SimulationObjectAndABCMeta(SimulationObjMeta, ConcreteABCMeta):
    """ A concrete class based on two Meta classes to be used as a metaclass for classes derived from both
    """
    pass


class SimulationObject(BaseSimulationObject, SimulationObjectInterface, metaclass=SimulationObjectAndABCMeta):
    """ Base class for all simulation objects in a simulation

    Attributes:
        metadata (:obj:`SimulationObjectMetadata`): metadata for event message sending and handling,
            initialized by :obj:`SimulationObjectAndABCMeta`
    """

    def init_before_run(self):
        """ Perform initialization before a simulation run

        If a simulation object defines `init_before_run`, it will be called by the simulator just before
        simulation begins, after all simulation objects have been created and loaded.
        A simulation object that wishes to schedule initial events for itself or for other objects in the simulation
        should do so in `init_before_run`. It can also perform any other initialization in the method.
        """
        pass  # pragma: no cover

    @classmethod
    def set_class_priority(cls, priority):
        """ Set the execution priority for a simulation object class, `class_priority`

        Use this to set the `class_priority` of a subclass of :class:`BaseSimulationObject` after it
        has been constructed.

        Args:
            priority (:obj:`SimObjClassPriority`): the desired `class_priority` for a subclass
                of :class:`BaseSimulationObject`
        """
        setattr(cls.metadata, SimulationObjMeta.CLASS_PRIORITY, priority)
