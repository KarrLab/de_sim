""" Discrete event simulator

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-06-01
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

from collections import Counter, namedtuple
from datetime import datetime
import cProfile
import heapq
import math
import os
import pstats
import tempfile

from de_sim.config import core
from de_sim.event import Event
from de_sim.event_message import EventMessage
from de_sim.simulation_metadata import SimulationMetadata, RunMetadata, AuthorMetadata
from de_sim.errors import SimulatorError
from de_sim.simulation_config import SimulationConfig
from de_sim.utilities import SimulationProgressBar, FastLogger
from wc_utils.util.git import get_repo_metadata, RepoMetadataCollectionType
from wc_utils.util.list import elements_to_str


class EventQueue(object):
    """ A simulation's event queue

    Stores a :obj:`Simulator`'s events in a heap (also known as a priority queue).
    The heap is a 'min heap', which keeps the event with the smallest sort order at the root in `heap[0]`.
    :obj:`~de_sim.event.Event`\ s are sorted on their `_get_order_time`, which provides a pair, (event time, event 'sub-time'),
    and is implemented via comparison operations in :obj:`~de_sim.event.Event`.
    All entries with equal `(event time, event 'sub-time')` values are popped from the heap by `next_events()`.
    `schedule_event()` costs `O(log(n))`, where `n` is the size of the heap,
    while `next_events()`, costs `O(mlog(n))`, where `m` is the number of events returned.

    Attributes:
        event_heap (:obj:`list`): a :obj:`Simulator`'s heap of events
        debug_logs (:obj:`wc_utils.debug_logs.core.DebugLogsManager`): a `DebugLogsManager`
    """

    def __init__(self):
        self.event_heap = []
        self.debug_logs = core.get_debug_logs()
        self.fast_debug_file_logger = FastLogger(self.debug_logs.get_log('de_sim.debug.file'), 'debug')

    def reset(self):
        """ Empty the event queue
        """
        self.event_heap = []

    def len(self):
        """ Size of the event queue

        Returns:
            :obj:`int`: number of events in the event queue
        """
        return len(self.event_heap)

    def schedule_event(self, send_time, receive_time, sending_object, receiving_object, event_message):
        """ Create an event scheduled to execute at `receive_time` and insert in this event queue

        Args:
            send_time (:obj:`float`): the simulation time at which the event was generated (sent)
            receive_time (:obj:`float`): the simulation time at which the `receiving_object` will
                execute the event
            sending_object (:obj:`~de_sim.simulation_object.SimulationObject`): the object sending the event
            receiving_object (:obj:`~de_sim.simulation_object.SimulationObject`): the object that will receive the
                event; when the simulation is parallelized `sending_object` and `receiving_object` will need
                to be global identifiers.
            event_message (:obj:`~de_sim.event_message.EventMessage`): an event message carried by the event; its type
                provides the simulation application's type for an :obj:`~de_sim.event.Event`; it may also carry a
                payload for the :obj:`~de_sim.event.Event` in its attributes.

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

        if not isinstance(event_message, EventMessage):
            raise SimulatorError("event_message should be an instance of {} but is a '{}'".format(
                EventMessage.__name__, type(event_message).__name__))

        event = Event(send_time, receive_time, sending_object, receiving_object, event_message)
        # As per David Jefferson's thinking, the event queue is ordered by data provided by the
        # simulation application, in particular the tuple (event time, receiving object name).
        # See the comparison operators for Event. This achieves deterministic and reproducible
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
            :obj:`~de_sim.simulation_object.SimulationObject`: the simulation object that will execute the next event,
            or `None` if no event is scheduled
        """
        if not self.event_heap:
            return None

        next_event = self.event_heap[0]
        return next_event.receiving_object

    def next_events(self):
        """ Get all events at the smallest event time destined for the simulation object with the highest priority

        If one event has the smallest `event_time`, which occurs often, it is returned in a :obj:`list`.

        But because multiple events may occur simultaneously -- that is, have the same `event_time` --
        they are returned in a list that will be passed to the simulation object that will handle them.
        Specifically, if an :obj:`EventQueue` contains multiple events with the same `event_time` and they
        will be received by multiple
        simulation objects, then the event(s) scheduled for the highest priority simulation object will be
        returned. Subsequent calls to `next_events` will return events schedule for simulation object(s) with lower
        priority(s).

        If multiple events are returned, they are sorted by the pair (event message type priority,
        event message field values).

        Returns:
            :obj:`list` of :obj:`~de_sim.event.Event`: the earliest event(s); if no events are available the list is empty
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
        """ Log an event with its simulation time to the `fast_debug_file_logger`

        Args:
            event (:obj:`~de_sim.event.Event`): the Event to log
        """
        msg = "Execute: {} {}:{} {} ({})".format(event.event_time,
                                                 type(event.receiving_object).__name__,
                                                 event.receiving_object.name,
                                                 event.message.__class__.__name__,
                                                 str(event.message))
        self.fast_debug_file_logger.fast_log(msg, sim_time=event.event_time)

    def render(self, sim_obj=None, as_list=False, separator='\t'):
        """ Return the content of an :obj:`EventQueue`

        Make a human-readable event queue, sorted by event time.
        Events are sorted by the event order tuple provided by `Event._get_order_time`.
        Provide a header row and a row for each event. If all events have the same type of message,
        the header contains event and message fields. Otherwise, the header has event fields and
        a message field label, and each event labels message fields with their attribute names.

        Args:
            sim_obj (:obj:`~de_sim.simulation_object.SimulationObject`, optional): if provided, return only events to be
                received by `sim_obj`
            as_list (:obj:`bool`, optional): if set, return the :obj:`EventQueue`'s values in a :obj:`list`
            separator (:obj:`str`, optional): the field separator used if the values are returned as
                a string

        Returns:
            :obj:`str`: String representation of the values of an :obj:`EventQueue`, or a :obj:`list`
            representation if `as_list` is set
        """
        event_heap = self.event_heap
        if sim_obj is not None:
            event_heap = list(filter(lambda event: event.receiving_object == sim_obj, event_heap))

        if not event_heap:
            return None

        # Sort the events by the event order tuple, provided by `Event._get_order_time`
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


class Simulator(object):
    """ A discrete-event simulator

    A general-purpose discrete-event simulation mechanism, including the simulation scheduler.
    Architected as an object-oriented simulation that could be parallelized.

    :obj:`Simulator` contains and manipulates global simulation data.
    :obj:`Simulator` registers all simulation objects classes and all simulation objects.
    The `simulate()` method runs a simulation, scheduling objects to execute events
    in non-decreasing time order, and generates debugging output.

    Attributes:
        time (:obj:`float`): a simulation's current time
        simulation_objects (:obj:`dict` of :obj:`~de_sim.simulation_object.SimulationObject`): all simulation objects,
            keyed by their names
        debug_logs (:obj:`wc_utils.debug_logs.core.DebugLogsManager`): the debug logs
        fast_debug_file_logger (:obj:`~de_sim.utilities.FastLogger`): a fast logger for debugging messages
        fast_plotting_logger (:obj:`~de_sim.utilities.FastLogger`): a fast logger that saves trajectory data for
            plotting
        event_queue (:obj:`EventQueue`): the queue of events that will be executed
        event_counts (:obj:`Counter`): a count of executed events, categorized by the tuple
            (receiving object class, receiving object name, event message class)
        num_handlers_called (:obj:`int`): the number of calls a simulation makes to an event handler in a
            simulation object
        sim_config (:obj:`~de_sim.simulation_config.SimulationConfig`): a simulation run's configuration
        sim_metadata (:obj:`~de_sim.simulation_metadata.SimulationMetadata`): a simulation run's metadata
        author_metadata (:obj:`~de_sim.simulation_metadata.AuthorMetadata`): information about the person who runs the
            simulation, if provided by the simulation application
        measurements_fh (:obj:`_io.TextIOWrapper`): file handle for debugging measurements file
        mem_tracker (:obj:`pympler.tracker.SummaryTracker`): a memory use tracker for debugging
    """
    # Termination messages
    NO_EVENTS_REMAIN = " No events remain"
    END_TIME_EXCEEDED = " End time exceeded"
    TERMINATE_WITH_STOP_CONDITION_SATISFIED = " Terminate with stop condition satisfied"

    # number of rows to print in a performance profile
    NUM_PROFILE_ROWS = 50

    def __init__(self):
        self.debug_logs = core.get_debug_logs()
        self.fast_debug_file_logger = FastLogger(self.debug_logs.get_log('de_sim.debug.file'), 'debug')
        self.fast_plotting_logger = FastLogger(self.debug_logs.get_log('de_sim.plot.file'), 'debug')
        # self.time is not known until a simulation starts
        self.time = None
        self.simulation_objects = {}
        self.event_queue = EventQueue()
        self.event_counts = Counter()
        self.__initialized = False

    def add_object(self, simulation_object):
        """ Add a simulation object instance to this simulation

        Args:
            simulation_object (:obj:`~de_sim.simulation_object.SimulationObject`): a simulation object instance that
                will be used by this simulation

        Raises:
            :obj:`SimulatorError`: if the simulation object's name is already in use
        """
        name = simulation_object.name
        if name in self.simulation_objects:
            raise SimulatorError("cannot add simulation object '{}', name already in use".format(name))
        simulation_object.set_simulator(self)
        self.simulation_objects[name] = simulation_object

    def add_objects(self, simulation_objects):
        """ Add multiple simulation objects to this simulation

        Args:
            simulation_objects (:obj:`iterator` of :obj:`~de_sim.simulation_object.SimulationObject`):
                an iterator over simulation objects
        """
        for simulation_object in simulation_objects:
            self.add_object(simulation_object)

    def get_object(self, simulation_object_name):
        """ Get a simulation object used by this simulation

        Args:
            simulation_object_name (:obj:`str`): the name of a simulation object

        Returns:
            :obj:`~de_sim.simulation_object.SimulationObject`: the simulation object whose
            name is `simulation_object_name`

        Raises:
            :obj:`SimulatorError`: if the simulation object whose name is `simulation_object_name`
            is not used by this simulation
        """
        if simulation_object_name not in self.simulation_objects:
            raise SimulatorError("cannot get simulation object '{}'".format(simulation_object_name))
        return self.simulation_objects[simulation_object_name]

    def get_objects(self):
        """ Get all simulation object instances in this simulation

        Returns:
            :obj:`iterator` over :obj:`~de_sim.simulation_object.SimulationObject`: an iterator over
            all simulation object instances in this simulation
        """
        # This is reproducible for Python 3.7 and later (see https://docs.python.org/3/whatsnew/3.7.html)
        # TODO(Arthur): eliminate external calls to self.simulator.simulation_objects
        return self.simulation_objects.values()

    def _delete_object(self, simulation_object):
        """ Delete a simulation object instance from this simulation

        This method should not be called by :obj:`~de_sim.simulation_object.SimulationObject`\ s.

        Args:
            simulation_object (:obj:`~de_sim.simulation_object.SimulationObject`): a simulation object instance
            that is part of this simulation

        Raises:
            :obj:`SimulatorError`: if the simulation object is not part of this simulation
        """
        # prohibit calls to _delete_object while a simulation is running
        # more precisely, prohibit between a simulation's initialization & reset
        if self.__initialized:
            raise SimulatorError(f"cannot delete simulation object: simulator is between "
                                 f"initialize and reset")
        name = simulation_object.name
        if name not in self.simulation_objects:
            raise SimulatorError(f"cannot delete simulation object '{name}', it has not been added")
        simulation_object.del_simulator()
        del self.simulation_objects[name]

    def initialize(self):
        """ Initialize a simulation

        Call `init_before_run()` in each simulation object that has been loaded.

        Raises:
            :obj:`SimulatorError`:  if the simulation has already been initialized
        """
        if self.__initialized:
            raise SimulatorError('Simulation has already been initialized')
        for sim_obj in self.simulation_objects.values():
            sim_obj.init_before_run()
        self.event_counts.clear()
        self.__initialized = True

    def init_metadata_collection(self, sim_config):
        """ Initialize this simulation's metadata object

        Call just before a simulation runs, so that the correct start time of the simulation is recorded

        Args:
            sim_config (:obj:`~de_sim.simulation_config.SimulationConfig`): metadata about the simulation's
            configuration (start time, maximum time, etc.)
        """
        if self.author_metadata is None:
            author = AuthorMetadata()
        else:
            author = self.author_metadata
        run = RunMetadata()
        run.record_ip_address()
        run.record_start()

        # obtain repo metadaa, if possible
        simulator_repo = None
        try:
            simulator_repo, _ = get_repo_metadata(repo_type=RepoMetadataCollectionType.SCHEMA_REPO)
        except ValueError:
            pass
        self.sim_metadata = SimulationMetadata(simulation_config=sim_config, run=run, author=author,
                                               simulator_repo=simulator_repo)

    def finish_metadata_collection(self):
        """ Finish metadata collection: record a simulation's runtime, and write all metadata to disk
        """
        self.sim_metadata.run.record_run_time()
        if self.sim_config.output_dir:
            SimulationMetadata.write_dataclass(self.sim_metadata, self.sim_config.output_dir)

    def reset(self):
        """ Reset this :obj:`Simulator`

        Delete all objects, and empty the event queue.
        """
        self.__initialized = False
        for simulation_object in list(self.simulation_objects.values()):
            self._delete_object(simulation_object)
        self.event_queue.reset()
        self.time = None

    def message_queues(self):
        """ Return a string listing all message queues in the simulation, organized by simulation object

        Returns:
            :obj:`str`: a list of all message queues in the simulation and their messages
        """
        now = "'uninitialized'"
        if self.time is not None:
            now = f"{self.time:6.3f}"

        data = [f'Event queues at {now}']
        for sim_obj in sorted(self.simulation_objects.values(), key=lambda sim_obj: sim_obj.name):
            data.append(sim_obj.name + ':')
            rendered_eq = self.event_queue.render(sim_obj=sim_obj)
            if rendered_eq is None:
                data.append('Empty event queue')
            else:
                data.append(rendered_eq)
            data.append('')
        return '\n'.join(data)

    @staticmethod
    def get_sim_config(max_time=None, sim_config=None, config_dict=None):
        """ External simulate interface

        Legal combinations of the three parameters:

        1. Just `max_time`
        2. Just `sim_config`, which will contain an entry for `max_time`
        3. Just `config_dict`, which must contain an entry for `max_time`

        Other combinations are illegal.

        Args:
            max_time (:obj:`float`, optional): the time of the end of the simulation
            sim_config (:obj:`~de_sim.simulation_config.SimulationConfig`, optional): the simulation
                run's configuration
            config_dict (:obj:`dict`, optional): a dictionary with keys chosen from the field names
                in :obj:`~de_sim.simulation_config.SimulationConfig`; note that `config_dict`
                is not a `kwargs` argument

        Returns:
            :obj:`~de_sim.simulation_config.SimulationConfig`: a validated simulation configuration

        Raises:
            :obj:`SimulatorError`: if no arguments are provided, or multiple arguments are provided,
                or `max_time` is missing from `config_dict`
        """
        num_args = 0
        if max_time is not None:
            num_args += 1
        if sim_config is not None:
            num_args += 1
        if config_dict:
            num_args += 1
        if num_args == 0:
            raise SimulatorError('max_time, sim_config, or config_dict must be provided')
        if 1 < num_args:
            raise SimulatorError('at most 1 of max_time, sim_config, or config_dict may be provided')

        # catch common error generated when sim_config= is not used by Simulator.simulate(sim_config)
        if isinstance(max_time, SimulationConfig):
            raise SimulatorError(f"sim_config is not provided, sim_config= is probably needed")

        # initialize sim_config if it is not provided
        if sim_config is None:
            if max_time is not None:
                sim_config = SimulationConfig(max_time)
            else:   # config_dict must be initialized
                if 'max_time' not in config_dict:
                    raise SimulatorError('max_time must be provided in config_dict')
                sim_config = SimulationConfig(**config_dict)

        sim_config.validate()
        return sim_config

    SimulationReturnValue = namedtuple('SimulationReturnValue', 'num_events profile_stats',
                                       defaults=(None, None))
    SimulationReturnValue.__doc__ += ': the value(s) returned by a simulation run'
    SimulationReturnValue.num_events.__doc__ += (": the number of times a simulation object handles an event, "
                                                 "which may be smaller than the number of events sent, because simultaneous "
                                                 "events at a simulation object are handled together")
    SimulationReturnValue.profile_stats.__doc__ += (": if performance is being profiled, a :obj:`pstats.Stats` instance "
                                                    "containing the profiling statistics")

    def simulate(self, max_time=None, sim_config=None, config_dict=None, author_metadata=None):
        """ Run a simulation

        Exactly one of the arguments `max_time`, `sim_config`, and `config_dict` must be provided.
        See `get_sim_config` for additional constraints on these arguments.

        Args:
            max_time (:obj:`float`, optional): the maximum time of the end of the simulation
            sim_config (:obj:`~de_sim.simulation_config.SimulationConfig`, optional): a simulation run's configuration
            config_dict (:obj:`dict`, optional): a dictionary with keys chosen from
                the field names in :obj:`~de_sim.simulation_config.SimulationConfig`
            author_metadata (:obj:`~de_sim.simulation_metadata.AuthorMetadata`, optional): information about the
                person who runs the simulation; if not provided, then the their username will be obtained automatically

        Returns:
            :obj:`SimulationReturnValue`: a :obj:`SimulationReturnValue` whose fields are documented with its definition

        Raises:
            :obj:`SimulatorError`: if the simulation has not been initialized, or has no objects,
                or has no initial events, or attempts to execute an event that violates non-decreasing time
                order
        """
        self.sim_config = self.get_sim_config(max_time=max_time, sim_config=sim_config,
                                               config_dict=config_dict)
        self.author_metadata = author_metadata
        if self.sim_config.output_dir:
            measurements_file = core.get_config()['de_sim']['measurements_file']
            self.measurements_fh = open(os.path.join(self.sim_config.output_dir, measurements_file), 'w')
            print(f"de_sim measurements: {datetime.now().isoformat(' ')}", file=self.measurements_fh)

        profile = None
        if self.sim_config.profile:
            # profile the simulation and return the profile object
            with tempfile.NamedTemporaryFile() as file_like_obj:
                out_file = file_like_obj.name
                locals = {'self': self}
                cProfile.runctx('self._simulate()', {}, locals, filename=out_file)
                if self.sim_config.output_dir:
                    profile = pstats.Stats(out_file, stream=self.measurements_fh)
                else:
                    profile = pstats.Stats(out_file)
                profile.sort_stats('tottime').print_stats(self.NUM_PROFILE_ROWS)
        else:
            self._simulate()
        if self.sim_config.output_dir:
            self.measurements_fh.close()
        return self.SimulationReturnValue(self.num_handlers_called, profile)

    def run(self, max_time=None, sim_config=None, config_dict=None, author_metadata=None):
        """ Alias for `simulate`
        """
        return self.simulate(max_time=max_time, sim_config=sim_config, config_dict=config_dict,
                             author_metadata=author_metadata)

    def _simulate(self):
        """ Run the simulation

        Returns:
            :obj:`int`: the number of times a simulation object executes `_handle_event()`. This may
            be smaller than the number of events sent, because simultaneous events at one
            simulation object are handled together.

        Raises:
            :obj:`SimulatorError`: if the simulation has not been initialized, or has no objects,
                or has no initial events, or attempts to start before the start time in `time_init`,
                or attempts to execute an event that violates non-decreasing time order
        """
        if not self.__initialized:
            raise SimulatorError("Simulation has not been initialized")

        if not len(self.get_objects()):
            raise SimulatorError("Simulation has no objects")

        if self.event_queue.empty():
            raise SimulatorError("Simulation has no initial events")

        _object_mem_tracking = False
        if 0 < self.sim_config.object_memory_change_interval:
            _object_mem_tracking = True
            # don't import tracker unless it's being used
            from pympler import tracker
            self.mem_tracker = tracker.SummaryTracker()

        # set simulation time to `time_init`
        self.time = self.sim_config.time_init

        # error if first event occurs before time_init
        next_time = self.event_queue.next_event_time()
        if next_time < self.sim_config.time_init:
            raise SimulatorError(f"Time of first event ({next_time}) is earlier than the start time "
                                 f"({self.sim_config.time_init})")

        # set up progress bar
        self.progress = SimulationProgressBar(self.sim_config.progress)

        # write header to a plot log
        # plot logging is controlled by configuration files pointed to by config_constants and by env vars
        self.fast_plotting_logger.fast_log('# {:%Y-%m-%d %H:%M:%S}'.format(datetime.now()), sim_time=0)

        self.num_handlers_called = 0
        self.log_with_time(f"Simulation to {self.sim_config.max_time} starting")

        try:
            self.progress.start(self.sim_config.max_time)
            self.init_metadata_collection(self.sim_config)

            while True:

                # use the stop condition
                if self.sim_config.stop_condition is not None and self.sim_config.stop_condition(self.time):
                    self.log_with_time(self.TERMINATE_WITH_STOP_CONDITION_SATISFIED)
                    self.progress.end()
                    break

                # if tracking object use, record object and memory use changes
                if _object_mem_tracking:
                    self.track_obj_mem()

                # get the earliest next event in the simulation
                # get parameters of next event from self.event_queue
                next_time = self.event_queue.next_event_time()
                next_sim_obj = self.event_queue.next_event_obj()

                if float('inf') == next_time:
                    self.log_with_time(self.NO_EVENTS_REMAIN)
                    self.progress.end()
                    break

                if self.sim_config.max_time < next_time:
                    self.log_with_time(self.END_TIME_EXCEEDED)
                    self.progress.end()
                    break

                self.time = next_time

                # error will only be raised if an object decreases its time
                if next_time < next_sim_obj.time:
                    raise SimulatorError("Dispatching '{}', but event time ({}) "
                                         "< object time ({})".format(next_sim_obj.name, next_time, next_sim_obj.time))

                # dispatch object that's ready to execute next event
                next_sim_obj.time = next_time

                self.log_with_time(" Running '{}' at {}".format(next_sim_obj.name, next_sim_obj.time))
                next_events = self.event_queue.next_events()
                for e in next_events:
                    e_name = ' - '.join([next_sim_obj.__class__.__name__, next_sim_obj.name, e.message.__class__.__name__])
                    self.event_counts[e_name] += 1
                next_sim_obj._BaseSimulationObject__handle_event_list(next_events)
                self.num_handlers_called += 1
                self.progress.progress(next_time)

        except SimulatorError as e:
            raise SimulatorError('Simulation ended with error:\n' + str(e))

        self.finish_metadata_collection()
        return self.num_handlers_called

    def track_obj_mem(self):
        """ Write memory use tracking data to the measurements file in `measurements_fh`
        """
        def format_row(values, widths=(60, 10, 16)):
            widths_format = "{{:<{}}}{{:>{}}}{{:>{}}}".format(*widths)
            return widths_format.format(*values)

        if self.num_handlers_called % self.sim_config.object_memory_change_interval == 0:
            heading = f"\nMemory use changes by SummaryTracker at event {self.num_handlers_called}:"
            if self.sim_config.output_dir:
                print(heading, file=self.measurements_fh)
                data_heading = ('type', '# objects', 'total size (B)')
                print(format_row(data_heading), file=self.measurements_fh)

                # mem_values = obj_type, count, mem
                for mem_values in sorted(self.mem_tracker.diff(), key=lambda mem_values: mem_values[2],
                                         reverse=True):
                    row = [str(val) for val in mem_values]
                    print(format_row(row), file=self.measurements_fh)
            else:
                print(heading)
                self.mem_tracker.print_diff()

    def log_with_time(self, msg):
        """ Write a debug log message with the simulation time.
        """
        self.fast_debug_file_logger.fast_log(msg, sim_time=self.time)

    def provide_event_counts(self):
        """ Provide the simulation's event counts, categorized by object type, object name, event type

        Returns:
            :obj:`str`: the simulation's categorized event counts, in a tab-separated table
        """
        rv = ['\t'.join(['Count', 'Event type (Object type - object name - event type)'])]
        for event_type, count in self.event_counts.most_common():
            rv.append("{}\t{}".format(count, event_type))
        return '\n'.join(rv)
