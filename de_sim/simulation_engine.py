""" Discrete event simulation engine

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-06-01
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from collections import Counter
import dataclasses
import datetime
import sys

from de_sim.config import core
from de_sim.simulation_metadata import SimulationMetadata, RunMetadata, AuthorMetadata
from de_sim.errors import SimulatorError
from de_sim.event import Event
from de_sim.shared_state_interface import SharedStateInterface
from de_sim.simulation_config import SimulationConfig
from de_sim.simulation_object import EventQueue, SimulationObject
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
        simulation_objects (:obj:`dict` of `SimulationObject`): all simulation objects, keyed by name
        shared_state (:obj:`list` of :obj:`object`, optional): the shared state of the simulation, needed to
            log or checkpoint the entire state of a simulation; all objects in `shared_state` must
            implement `SharedStateInterface`
        debug_logs (:obj:`wc_utils.debug_logs.core.DebugLogsManager`): the debug logs
        fast_debug_file_logger (:obj:`FastLogger`): a fast logger for debugging messages
        fast_plotting_logger (:obj:`FastLogger`): a fast logger for trajectory data for plotting
        event_queue (:obj:`EventQueue`): the queue of future events
        event_counts (:obj:`Counter`): a counter of event types
        sim_config (:obj:`SimulationConfig`, optional): a simulation run's configuration
    """
    # Termination messages
    NO_EVENTS_REMAIN = " No events remain"
    END_TIME_EXCEEDED = " End time exceeded"
    TERMINATE_WITH_STOP_CONDITION_SATISFIED = " Terminate with stop condition satisfied"

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
            simulation_objects (:obj:`iterator` of `SimulationObject`): an iterator of simulation objects
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

        Call `send_initial_events()` in each simulation object that has been loaded.

        Raises:
            :obj:`SimulatorError`:  if the simulation has already been initialized
        """
        if self.__initialized:
            raise SimulatorError('Simulation has already been initialized')
        for sim_obj in self.simulation_objects.values():
            sim_obj.send_initial_events()
        self.event_counts.clear()
        self.__initialized = True

    def init_metadata_collection(self, sim_config):
        """ Initialize metatdata collection

        Call just before simulation starts, so that correct clock time of start is recorded

        Args:
            sim_config (:obj:`SimulationConfig`): information about the simulation's configuration
                (start time, maximum time, etc.)
        """
        application, _ = get_repo_metadata(repo_type=RepoMetadataCollectionType.SCHEMA_REPO)
        author = AuthorMetadata()
        run = RunMetadata()
        run.record_ip_address()
        run.record_start()
        self.metadata = SimulationMetadata(application, sim_config, run, author)

    def finish_metadata_collection(self):
        """ Finish metatdata collection
        """
        self.metadata.run.record_run_time()
        if self.sim_config.metadata_dir:
            SimulationMetadata.write_metadata(self.metadata, self.sim_config.metadata_dir)

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

        Legal parameter combinations:

        1. Just `time_max`
        2. Just `sim_config`
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
            else:   # config_dict must be set
                if 'time_max' not in config_dict:
                    raise SimulatorError('time_max must be provided in config_dict')
                sim_config = SimulationConfig(**config_dict)

        sim_config.validate()
        return sim_config

    def simulate(self, time_max=None, sim_config=None, config_dict=None):
        """ Run a simulation

        See `_get_sim_config` for constraints on arguments

        Args:
            time_max (:obj:`float`, optional): the time of the end of the simulation
            sim_config (:obj:`SimulationConfig`, optional): the simulation run's configuration
            config_dict (:obj:`dict`, optional): a dictionary with keys chosen from
                the field names in :obj:`SimulationConfig`

        Returns:
            :obj:`int`: the number of times a simulation object executes `_handle_event()`. This may
                be smaller than the number of events sent, because simultaneous events at one
                simulation object are handled together.

        Raises:
            :obj:`SimulatorError`: if the simulation has not been initialized, or has no objects,
                or has no initial events, or attempts to execute an event that violates non-decreasing time
                order
        """
        self.sim_config = self._get_sim_config(time_max=time_max, sim_config=sim_config,
                                               config_dict=config_dict)
        return self._simulate()

    def run(self, time_max=None, sim_config=None, config_dict=None):
        """ Alias for simulate
        """
        return self.simulate(time_max=time_max, sim_config=sim_config, config_dict=config_dict)

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
        self.fast_plotting_logger.fast_log('# {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()), sim_time=0)

        num_events_handled = 0
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

                num_events_handled += 1

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
                next_sim_obj.__handle_event_list(next_events)
                self.progress.progress(next_time)

        except SimulatorError as e:
            raise SimulatorError('Simulation ended with error:\n' + str(e))

        self.finish_metadata_collection()
        return num_events_handled

    def log_with_time(self, msg):
        """Write a debug log message with the simulation time.
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
