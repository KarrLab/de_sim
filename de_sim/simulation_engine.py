""" Discrete event simulation engine

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-06-01
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

from collections import Counter, namedtuple
from datetime import datetime
import cProfile
import os
import pstats
import tempfile

from de_sim.config import core
from de_sim.simulation_metadata import SimulationMetadata, RunMetadata, AuthorMetadata
from de_sim.errors import SimulatorError
from de_sim.shared_state_interface import SharedStateInterface  # noqa: F401
from de_sim.simulation_config import SimulationConfig
from de_sim.simulation_object import EventQueue, SimulationObject  # noqa: F401
from de_sim.utilities import SimulationProgressBar, FastLogger
from wc_utils.util.git import get_repo_metadata, RepoMetadataCollectionType


class SimulationEngine(object):
    """ A simulation engine

    General-purpose simulation mechanisms, including the simulation scheduler.
    Architected as an OO simulation that could be parallelized.

    `SimulationEngine` contains and manipulates global simulation data.
    SimulationEngine registers all simulation objects types and all simulation objects.
    Following `simulate()` it runs the simulation, scheduling objects to execute events
    in non-decreasing time order; and generates debugging output.

    Attributes:
        time (:obj:`float`): the simulations's current time
        simulation_objects (:obj:`dict` of :obj:`SimulationObject`): all simulation objects, keyed by name
        shared_state (:obj:`list` of :obj:`object`, optional): the shared state of the simulation, needed to
            log or checkpoint the entire state of a simulation; all objects in `shared_state` must
            implement :obj:`SharedStateInterface`
        debug_logs (:obj:`wc_utils.debug_logs.core.DebugLogsManager`): the debug logs
        fast_debug_file_logger (:obj:`FastLogger`): a fast logger for debugging messages
        fast_plotting_logger (:obj:`FastLogger`): a fast logger for trajectory data for plotting
        event_queue (:obj:`EventQueue`): the queue of future events
        event_counts (:obj:`Counter`): a counter of event types
        num_events_handled (:obj:`int`): the number of events in a simulation
        sim_config (:obj:`SimulationConfig`): a simulation run's configuration
        sim_metadata (:obj:`SimulationMetadata`): a simulation run's metadata
        author_metadata (:obj:`AuthorMetadata`): information about the person who runs the simulation,
            if provided by the simulation application
        measurements_fh (:obj:`_io.TextIOWrapper`, optional): file handle for debugging measurements file
        mem_tracker (:obj:`pympler.tracker.SummaryTracker`, optional): a memory use tracker for debugging
    """
    # Termination messages
    NO_EVENTS_REMAIN = " No events remain"
    END_TIME_EXCEEDED = " End time exceeded"
    TERMINATE_WITH_STOP_CONDITION_SATISFIED = " Terminate with stop condition satisfied"

    # number of rows to print in a performance profile
    NUM_PROFILE_ROWS = 50

    def __init__(self, shared_state=None):
        if shared_state is None:
            self.shared_state = []
        else:
            self.shared_state = shared_state
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
            simulation_object (:obj:`SimulationObject`): a simulation object instance that
                will be used by this simulation

        Raises:
            :obj:`SimulatorError`: if the simulation object's name is already in use
        """
        name = simulation_object.name
        if name in self.simulation_objects:
            raise SimulatorError("cannot add simulation object '{}', name already in use".format(name))
        simulation_object.add(self)
        self.simulation_objects[name] = simulation_object

    def add_objects(self, simulation_objects):
        """ Add many simulation objects into the simulation

        Args:
            simulation_objects (:obj:`iterator` of :obj:`SimulationObject`): an iterator of simulation objects
        """
        for simulation_object in simulation_objects:
            self.add_object(simulation_object)

    def get_object(self, simulation_object_name):
        """ Get a simulation object instance

        Args:
            simulation_object_name (:obj:`str`): get a simulation object instance that is
                part of this simulation

        Raises:
            :obj:`SimulatorError`: if the simulation object is not part of this simulation
        """
        if simulation_object_name not in self.simulation_objects:
            raise SimulatorError("cannot get simulation object '{}'".format(simulation_object_name))
        return self.simulation_objects[simulation_object_name]

    def get_objects(self):
        """ Get all simulation object instances in the simulation
        """
        # TODO(Arthur): make this reproducible
        # TODO(Arthur): eliminate external calls to self.simulator.simulation_objects
        return self.simulation_objects.values()

    def delete_object(self, simulation_object):
        """ Delete a simulation object instance from this simulation

        Args:
            simulation_object (:obj:`SimulationObject`): a simulation object instance that is
                part of this simulation

        Raises:
            :obj:`SimulatorError`: if the simulation object is not part of this simulation
        """
        # TODO(Arthur): is this an operation that makes sense to support? if not, remove it; if yes,
        # remove all of this object's state from simulator, and test it properly
        name = simulation_object.name
        if name not in self.simulation_objects:
            raise SimulatorError("cannot delete simulation object '{}', has not been added".format(name))
        simulation_object.delete()
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
        """ Initialize a simulation metatdata object

        Call just before a simulation starts, so that correct clock time of start is recorded

        Args:
            sim_config (:obj:`SimulationConfig`): information about the simulation's configuration
                (start time, maximum time, etc.)
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
        """ Finish metatdata collection
        """
        self.sim_metadata.run.record_run_time()
        if self.sim_config.output_dir:
            SimulationMetadata.write_dataclass(self.sim_metadata, self.sim_config.output_dir)

    def reset(self):
        """ Reset this `SimulationEngine`

        Delete all objects and reset any prior initialization.
        """
        for simulation_object in list(self.simulation_objects.values()):
            self.delete_object(simulation_object)
        self.event_queue.reset()
        self.__initialized = False

    def message_queues(self):
        """ Return a string listing all message queues in the simulation

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
    def _get_sim_config(time_max=None, sim_config=None, config_dict=None):
        """ External simulate interface

        Legal combinations of the three parameters:

        1. Just `time_max`
        2. Just `sim_config`, which will contain an entry for `time_max`
        3. Just `config_dict`, which must contain an entry for `time_max`

        Other combinations are illegal.

        Args:
            time_max (:obj:`float`, optional): the time of the end of the simulation
            sim_config (:obj:`SimulationConfig`, optional): the simulation run's configuration
            config_dict (:obj:`dict`, optional): a dictionary with keys chosen from the field names
                in :obj:`SimulationConfig`; note that `config_dict` is not a `kwargs` argument

        Returns:
            :obj:`SimulationConfig`: a validated simulation configuration

        Raises:
            :obj:`SimulatorError`: if no arguments are provided, or multiple arguments are provided,
                or `time_max` is missing from `config_dict`
        """
        num_args = 0
        if time_max is not None:
            num_args += 1
        if sim_config is not None:
            num_args += 1
        if config_dict:
            num_args += 1
        if num_args == 0:
            raise SimulatorError('time_max, sim_config, or config_dict must be provided')
        if 1 < num_args:
            raise SimulatorError('at most 1 of time_max, sim_config, or config_dict may be provided')

        # catch common error generated when sim_config= is not used by SimulationEngine.simulate(sim_config)
        if isinstance(time_max, SimulationConfig):
            raise SimulatorError(f"sim_config is not provided, sim_config= is probably needed")

        # initialize sim_config if it is not provided
        if sim_config is None:
            if time_max is not None:
                sim_config = SimulationConfig(time_max)
            else:   # config_dict must be initialized
                if 'time_max' not in config_dict:
                    raise SimulatorError('time_max must be provided in config_dict')
                sim_config = SimulationConfig(**config_dict)

        sim_config.validate()
        return sim_config

    SimulationReturnValue = namedtuple('SimulationReturnValue', 'num_events profile_stats',
                                       defaults=(None, None))

    def simulate(self, time_max=None, sim_config=None, config_dict=None, author_metadata=None):
        """ Run a simulation

        See `_get_sim_config` for constraints on arguments

        Args:
            time_max (:obj:`float`, optional): the time of the end of the simulation
            sim_config (:obj:`SimulationConfig`, optional): the simulation run's configuration
            config_dict (:obj:`dict`, optional): a dictionary with keys chosen from
                the field names in :obj:`SimulationConfig`
            author_metadata (:obj:`AuthorMetadata`, optional): information about the person who runs the simulation

        Returns:
            :obj:`SimulationReturnValue`: a :obj:`namedtuple` which contains a) the number of times any
                simulation object executes `_handle_event()`, which may
                be smaller than the number of events sent, because simultaneous events at one
                simulation object are handled together, and b), if `sim_config.profile` is set,
                a :obj:`pstats.Stats` instance containing the profiling statistics

        Raises:
            :obj:`SimulatorError`: if the simulation has not been initialized, or has no objects,
                or has no initial events, or attempts to execute an event that violates non-decreasing time
                order
        """
        self.sim_config = self._get_sim_config(time_max=time_max, sim_config=sim_config,
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
        return self.SimulationReturnValue(self.num_events_handled, profile)

    def run(self, time_max=None, sim_config=None, config_dict=None, author_metadata=None):
        """ Alias for simulate
        """
        return self.simulate(time_max=time_max, sim_config=sim_config, config_dict=config_dict,
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

        self.num_events_handled = 0
        self.log_with_time(f"Simulation to {self.sim_config.time_max} starting")

        try:
            self.progress.start(self.sim_config.time_max)
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

                if self.sim_config.time_max < next_time:
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
                next_sim_obj._SimulationObject__handle_event_list(next_events)
                self.num_events_handled += 1
                self.progress.progress(next_time)

        except SimulatorError as e:
            raise SimulatorError('Simulation ended with error:\n' + str(e))

        self.finish_metadata_collection()
        return self.num_events_handled

    def track_obj_mem(self):
        """ Write memory use tracking
        """
        def format_row(values, widths=(60, 10, 16)):
            widths_format = "{{:<{}}}{{:>{}}}{{:>{}}}".format(*widths)
            return widths_format.format(*values)

        if self.num_events_handled % self.sim_config.object_memory_change_interval == 0:
            heading = f"\nMemory use changes by SummaryTracker at event {self.num_events_handled}:"
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
        """ Provide the simulation's categorized event counts

        Returns:
            :obj:`str`: the simulation's categorized event counts, in a tab-separated table
        """
        rv = ['\t'.join(['Count', 'Event type (Object type - object name - event type)'])]
        for event_type, count in self.event_counts.most_common():
            rv.append("{}\t{}".format(count, event_type))
        return '\n'.join(rv)

    def get_simulation_state(self):
        """ Get the simulation's state
        """
        # get simulation time
        state = [self.time]
        # get the state of all simulation object(s)
        sim_objects_state = []
        for simulation_object in self.simulation_objects.values():
            # get object name, type, current time, state
            state_entry = (simulation_object.__class__.__name__,
                           simulation_object.name,
                           simulation_object.time,
                           simulation_object.get_state(),
                           simulation_object.render_event_queue())
            sim_objects_state.append(state_entry)
        state.append(sim_objects_state)

        # get the shared state
        shared_objects_state = []
        for shared_state_obj in self.shared_state:
            state_entry = (shared_state_obj.__class__.__name__,
                           shared_state_obj.get_name(),
                           shared_state_obj.get_shared_state(self.time))
            shared_objects_state.append(state_entry)
        state.append(shared_objects_state)
        return state
