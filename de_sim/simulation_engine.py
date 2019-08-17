""" Core discrete event simulation engine

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-06-01
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import datetime
import pprint
import sys
from collections import Counter

from de_sim.simulation_object import EventQueue, SimulationObject
from de_sim.errors import SimulatorError
from de_sim.event import Event
from de_sim.shared_state_interface import SharedStateInterface
from de_sim.config import core


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
        debug_log (:obj:`bool`, optional): whether to output a debug log
        debug_logs (:obj:` TODO
        stop_condition (:obj:`function`, optional): if provided, a function that takes one argument:
            `time`; a simulation terminates if `stop_condition` returns `True`
        event_counts (:obj:`Counter`): a counter of event types
        __initialized (:obj:`bool`): whether the simulation has been initialized

        Raises:
            :obj:`SimulatorError`: if the `stop_condition` is not callable
    """

    def __init__(self, shared_state=None, debug_log=False, stop_condition=None):
        if shared_state is None:
            self.shared_state = []
        else:
            self.shared_state = shared_state
        self.debug_log = debug_log
        self.debug_logs = core.get_debug_logs()
        self.set_stop_condition(stop_condition)
        self.time = 0.0
        self.simulation_objects = {}
        self.log_with_time("SimulationEngine created")
        self.event_queue = EventQueue()
        self.event_counts = Counter()
        self.__initialized = False

    def set_stop_condition(self, stop_condition):
        """ Set the simulation engine's stop condition

        Attributes:
            stop_condition (:obj:`function`): a function that takes one argument
                `time`; `stop_condition` is executed and tested before each simulation event.
                If it returns `True` a simulation is terminated.

            Raises:
                :obj:`SimulatorError`: if the `stop_condition` is not callable
        """
        if stop_condition is not None and not callable(stop_condition):
            raise SimulatorError('stop_condition is not a function')
        self.stop_condition = stop_condition

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
            SimulatorError: if the simulation has already been initialized
        """
        if self.__initialized:
            raise SimulatorError('Simulation has already been initialized')
        for sim_obj in self.simulation_objects.values():
            sim_obj.send_initial_events()
        self.event_counts.clear()
        self.__initialized = True

    def reset(self):
        """ Reset this `SimulationEngine`

        Set simulation time to 0, delete all objects, and reset any prior initialization.
        """
        self.time = 0.0
        for simulation_object in list(self.simulation_objects.values()):
            self.delete_object(simulation_object)
        self.event_queue.reset()
        self.__initialized = False

    def message_queues(self):
        """ Return a string listing all message queues in the simulation

        Returns:
            :obj:`str`: a list of all message queues in the simulation and their messages
        """
        data = ['Event queues at {:6.3f}'.format(self.time)]
        for sim_obj in sorted(self.simulation_objects.values(), key=lambda sim_obj: sim_obj.name):
            data.append(sim_obj.name + ':')
            rendered_eq = self.event_queue.render(sim_obj=sim_obj)
            if rendered_eq is None:
                data.append('Empty event queue')
            else:
                data.append(rendered_eq)
            data.append('')
        return '\n'.join(data)

    def run(self, end_time, epsilon=None):
        """ Alias for simulate
        """
        return self.simulate(end_time, epsilon=epsilon)

    def simulate(self, end_time, epsilon=None, stop_condition=None):
        """ Run the simulation

        Args:
            end_time (:obj:`float`): the time of the end of the simulation
            epsilon (:obj:`float`): small time interval used to control the order of near simultaneous
                events at different simulation objects; if provided, compare
                `epsilon` with `end_time` to ensure the ratio is not too large.
            stop_condition (:obj:`function`, optional): if provided, a function that takes one argument
                `time`; a simulation terminates if the function returns `True`

        Returns:
            :obj:`int`: the number of times a simulation object executes `_handle_event()`. This may
                be smaller than the number of events sent, because simultaneous events are handled together.

        Raises:
            :obj:`SimulatorError`: if the ratio of `end_time` to `epsilon` is so large that `epsilon`
                is lost in roundoff error, or if the simulation has not been initialized
        """
        if not self.__initialized:
            raise SimulatorError("Simulation has not been initialized")

        if not len(self.get_objects()):
            raise SimulatorError("Simulation has no objects")

        if self.event_queue.empty():
            raise SimulatorError("Simulation has no events")

        # ratio of max simulation time to epsilon must not be so large that epsilon is lost
        # in roundoff error
        if not epsilon is None and not(epsilon + end_time > end_time):
            raise SimulatorError("epsilon ({:E}) plus end time ({:E}) must exceed end time".format(
                epsilon, end_time))

        if stop_condition is not None:
            self.set_stop_condition(stop_condition)

        # write header to a plot log
        # plot logging is controlled by configuration files pointed to by config_constants and by env vars
        plotting_logger = self.debug_logs.get_log('wc.plot.file')
        plotting_logger.debug('# {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()), sim_time=0)

        num_events_handled = 0
        self.log_with_time("Simulation to {} starting".format(end_time))

        try:
            while self.time <= end_time:
                # use the stop condition
                if self.stop_condition is not None and self.stop_condition(self.time):
                    self.log_with_time(" Terminate with stop condition satisfied")
                    break

                # TODO(Arthur): provide dynamic control
                # self.log_simulation_state()

                # get the earliest next event in the simulation
                self.log_with_time('Simulation Engine launching next object')
                # get parameters of next event from self.event_queue
                next_time = self.event_queue.next_event_time()
                next_sim_obj = self.event_queue.next_event_obj()

                if float('inf') == next_time:
                    self.log_with_time(" No events remain")
                    break

                if end_time < next_time:
                    self.log_with_time(" End time exceeded")
                    break

                num_events_handled += 1

                self.time = next_time

                # assertion won't be violated unless init message sent to negative time or
                # objects decrease their time.
                assert next_sim_obj.time <= next_time, ("Dispatching '{}', but object time "
                    "({}) <= event time ({}) is false".format(next_sim_obj.name, next_sim_obj.time, next_time))

                # dispatch object that's ready to execute next event
                next_sim_obj.time = next_time
                self.log_with_time(" Running '{}' at {}".format(next_sim_obj.name, next_sim_obj.time))
                next_events = self.event_queue.next_events()
                for e in next_events:
                    e_name = ' - '.join([next_sim_obj.__class__.__name__, next_sim_obj.name, e.message.__class__.__name__])
                    self.event_counts[e_name] += 1
                next_sim_obj.__handle_event_list(next_events)
        except SimulatorError as e:
            print('Simulation ended with error:', e, file=sys.stderr)

        return num_events_handled

    def log_with_time(self, msg, local_call_depth=1):
        """Write a debug log message with the simulation time.
        """
        self.debug_logs.get_log('wc.debug.file').debug(msg, sim_time=self.time,
            local_call_depth=local_call_depth)

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

    def log_simulation_state(self):
        """ Log the simulation's state
        """
        if not self.debug_log:
            return
        state = self.get_simulation_state()
        # TODO(Arthur): save this through a logger
        # print(pprint.pformat(state))
        return pprint.pformat(state)
