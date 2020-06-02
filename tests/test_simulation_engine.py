"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-03-26
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from capturer import CaptureOutput
from datetime import datetime
from logging2 import LogRegister
from logging2.levels import LogLevel
import cProfile
import os
import pstats
import random
import shutil
import sys
import tempfile
import time
import unittest
import warnings

from de_sim.config import core
from de_sim.simulation_metadata import SimulationMetadata, RunMetadata, AuthorMetadata
from de_sim.errors import SimulatorError
from de_sim.shared_state_interface import SharedStateInterface
from de_sim.simulation_config import SimulationConfig
from de_sim.simulation_engine import SimulationEngine
from de_sim.simulation_message import SimulationMessage
from de_sim.simulation_object import SimulationObject, ApplicationSimulationObject
from de_sim.template_sim_objs import TemplatePeriodicSimulationObject
from de_sim.testing.some_message_types import InitMsg, Eg1
from de_sim.utilities import FastLogger
from wc_utils.util.dict import DictUtil

ALL_MESSAGE_TYPES = [InitMsg, Eg1]


class BasicExampleSimulationObject(ApplicationSimulationObject):

    def __init__(self, name):
        SimulationObject.__init__(self, name)
        self.num = 0

    def send_initial_events(self):
        self.send_event(1, self, InitMsg())

    def get_state(self):
        return "self.num: {}".format(self.num)

    def handle_event(self, event): pass

    event_handlers = [(InitMsg, handle_event)]

    # register the message types sent
    messages_sent = ALL_MESSAGE_TYPES


class ExampleSimulationObject(BasicExampleSimulationObject):

    def handle_event(self, event):
        self.send_event(2.0, self, InitMsg())

    event_handlers = [(sim_msg_type, 'handle_event') for sim_msg_type in ALL_MESSAGE_TYPES]

    messages_sent = ALL_MESSAGE_TYPES


class InteractingSimulationObject(BasicExampleSimulationObject):

    def handle_event(self, event):
        self.num += 1
        # send an event to each object in the simulator
        for obj in self.simulator.simulation_objects.values():
            self.send_event(1, obj, InitMsg())

    event_handlers = [(sim_msg_type, 'handle_event') for sim_msg_type in ALL_MESSAGE_TYPES]

    messages_sent = ALL_MESSAGE_TYPES


class CyclicalMessagesSimulationObject(ApplicationSimulationObject):
    """ Send events around a cycle of objects
    """

    def __init__(self, name, obj_num, cycle_size, test_case):
        SimulationObject.__init__(self, name)
        self.obj_num = obj_num
        self.cycle_size = cycle_size
        self.test_case = test_case
        self.num_msgs = 0

    def next_obj(self):
        next = (self.obj_num+1) % self.cycle_size
        return self.simulator.simulation_objects[obj_name(next)]

    def send_initial_events(self):
        # send event to next CyclicalMessagesSimulationObject
        self.send_event(1, self.next_obj(), InitMsg())

    def handle_event(self, event):
        self.num_msgs += 1
        self.test_case.assertEqual(self.time, float(self.num_msgs))
        # send event to next CyclicalMessagesSimulationObject
        self.send_event(1, self.next_obj(), InitMsg())

    def get_state(self):
        return "self: obj_num: {} num_msgs: {}".format(self.obj_num, self.num_msgs)

    event_handlers = [(sim_msg_type, 'handle_event') for sim_msg_type in ALL_MESSAGE_TYPES]

    # register the message types sent
    messages_sent = ALL_MESSAGE_TYPES


class PeriodicSimulationObject(TemplatePeriodicSimulationObject):
    """ Self-clocking ApplicationSimulationObject

    Attributes:
        period (:obj:`float`): interval between events, in simulated time units
    """

    def __init__(self, name, period):
        super().__init__(name, period)

    def handle_event(self):
        """ Handle the periodic event
        """
        return


NAME_PREFIX = 'sim_obj'

def obj_name(i):
    return '{}_{}'.format(NAME_PREFIX, i)


class TestSimulationEngine(unittest.TestCase):

    def setUp(self):
        # create simulator
        self.simulator = SimulationEngine()
        self.out_dir = tempfile.mkdtemp()
        self.log_names = ['de_sim.debug.file', 'de_sim.plot.file']
        measurements_file = core.get_config()['de_sim']['measurements_file']
        self.measurements_pathname = os.path.join(self.out_dir, measurements_file)

    def tearDown(self):
        shutil.rmtree(self.out_dir)

    def make_one_object_simulation(self):
        self.simulator.reset()
        obj = ExampleSimulationObject(obj_name(1))
        self.simulator.add_object(obj)
        self.assertEqual(self.simulator.get_object(obj.name), obj)
        self.simulator.initialize()

    def test_get_sim_config(self):
        self.assertEqual(SimulationConfig(5.), SimulationEngine._get_sim_config(time_max=5.))

        config_dict = dict(time_max=5., time_init=2.)
        self.assertEqual(SimulationConfig(5., 2.), SimulationEngine._get_sim_config(config_dict=config_dict))

        with self.assertRaisesRegex(SimulatorError, 'time_max, sim_config, or config_dict must be provided'):
            SimulationEngine._get_sim_config()

        config_dict = dict(time_init=2.)
        with self.assertRaisesRegex(SimulatorError, 'at most 1 of time_max, sim_config, or config_dict'):
            SimulationEngine._get_sim_config(100, config_dict=config_dict)

        simulation_config = SimulationConfig(10)
        with self.assertRaisesRegex(SimulatorError,
                                    'sim_config is not provided, sim_config= is probably needed'):
            SimulationEngine._get_sim_config(simulation_config)

        config_dict = dict(time_init=2.)
        with self.assertRaisesRegex(SimulatorError, 'time_max must be provided in config_dict'):
            SimulationEngine._get_sim_config(config_dict=config_dict)

    def test_simulate_and_run(self):
        for operation in ['simulate', 'run']:
            self.make_one_object_simulation()
            expr = f'self.simulator.{operation}(5.0).num_events'
            self.assertEqual(eval(expr), 3)

    def test_one_object_simulation_neg_endtime(self):
        obj = ExampleSimulationObject(obj_name(1))
        self.simulator.add_object(obj)
        self.simulator.initialize()
        config_dict = dict(time_max=-1, time_init=-2)
        self.assertEqual(self.simulator.simulate(config_dict=config_dict).num_events, 0)

    def test_simulation_engine_exceptions(self):
        obj = ExampleSimulationObject(obj_name(1))
        with self.assertRaisesRegex(SimulatorError, f"cannot delete simulation object '{obj.name}'"):
            self.simulator.delete_object(obj)

        no_such_obj_name = 'no such object'
        with self.assertRaisesRegex(SimulatorError, f"cannot get simulation object '{no_such_obj_name}'"):
            self.simulator.get_object(no_such_obj_name)

        with self.assertRaisesRegex(SimulatorError, 'Simulation has not been initialized'):
            self.simulator.simulate(5.0)

        self.simulator.initialize()
        with self.assertRaisesRegex(SimulatorError, 'Simulation has no objects'):
            self.simulator.simulate(5.0)

        self.simulator.add_object(obj)
        with self.assertRaisesRegex(SimulatorError, 'Simulation has no initial events'):
            self.simulator.simulate(5.0)

        simulator = SimulationEngine()
        simulator.add_object(BasicExampleSimulationObject('test'))
        simulator.initialize()
        # start time = 2
        simulation_config = SimulationConfig(5, 2)
        with self.assertRaisesRegex(SimulatorError, 'first event .* is earlier than the start time'):
            simulator.simulate(sim_config=simulation_config)

        with self.assertRaisesRegex(SimulatorError, f"cannot add simulation object '{obj.name}'"):
            self.simulator.add_object(obj)

        self.simulator.delete_object(obj)
        try:
            self.simulator.add_object(obj)
        except:
            self.fail('should be able to add object after delete')

        self.simulator.reset()
        self.simulator.initialize()
        obj = ExampleSimulationObject(obj_name(2))
        self.simulator.add_object(obj)
        obj.time += 1
        event_queue = self.simulator.event_queue
        event_queue.schedule_event(0, 0, obj, obj, InitMsg())
        with self.assertRaisesRegex(SimulatorError, "but event time .* < object time"):
            self.simulator.simulate(5.0)

        with self.assertRaisesRegex(SimulatorError, 'Simulation has already been initialized'):
            self.simulator.initialize()

    def test_simulation_end(self):
        self.simulator.add_object(BasicExampleSimulationObject('name'))
        self.simulator.initialize()
        # TODO(Arthur): test that the "No events remain" message is logged
        self.simulator.simulate(5.0)

    def test_simulation_stop_condition(self):
        simulator = SimulationEngine()
        # 1 event/sec:
        simulator.add_object(PeriodicSimulationObject('name', 1))
        simulator.initialize()
        time_max = 10
        # execute to time <= time_max, with 1st event at time = 1
        self.assertEqual(simulator.simulate(time_max).num_events, time_max + 1)

        __stop_cond_end = 3
        def stop_cond_eg(time):
            return __stop_cond_end <= time
        simulator = SimulationEngine()
        simulator.add_object(PeriodicSimulationObject('name', 1))
        simulator.initialize()
        sim_config = SimulationConfig(time_max)
        sim_config.stop_condition = stop_cond_eg
        # because the simulation is executing one event / sec, the number of events should equal the stop time plus 1
        self.assertEqual(simulator.simulate(sim_config=sim_config).num_events, __stop_cond_end + 1)

    def test_progress_bar(self):
        simulator = SimulationEngine()
        simulator.add_object(PeriodicSimulationObject('name', 1))
        simulator.initialize()
        print('\nTesting progress bar:', file=sys.stderr)
        sys.stderr.flush()
        with CaptureOutput(relay=True) as capturer:
            try:
                time_max = 10
                config_dict = dict(time_max=time_max, progress=True)
                self.assertEqual(simulator.simulate(config_dict=config_dict).num_events, time_max + 1)
                self.assertTrue(f"/{time_max}" in capturer.get_text())
                self.assertTrue("time_max" in capturer.get_text())
            except ValueError as e:
                if str(e) == 'I/O operation on closed file':
                    pass
                    # This ValueError is raised because progressbar expects sys.stderr to remain open
                    # for an extended time period but karr_lab_build_utils run-tests has closed it.
                    # Since SimulationProgressBar works and passes tests under naked pytest, and
                    # progressbar does not want to address the conflict over sys.stderr
                    # (see https://github.com/WoLpH/python-progressbar/issues/202) we let this
                    # test fail under karr_lab_build_utils.
                else:
                    self.fail('test_progress failed for unknown reason')

    def test_multi_object_simulation_and_reset(self):
        for i in range(1, 4):
            obj = ExampleSimulationObject(obj_name(i))
            self.simulator.add_object(obj)
        self.simulator.initialize()
        self.assertEqual(self.simulator.simulate(5.0).num_events, 9)

        event_count_lines = self.simulator.provide_event_counts().split('\n')[1:]
        for idx, line in enumerate(event_count_lines):
            self.assertIn('3', line)
            self.assertIn('ExampleSimulationObject', line)
            self.assertIn(obj_name(idx+1), line)

        self.simulator.reset()
        self.assertEqual(len(self.simulator.simulation_objects), 0)

    def test_multi_interacting_object_simulation(self):
        sim_objects = [InteractingSimulationObject(obj_name(i)) for i in range(1, 3)]
        self.simulator.add_objects(sim_objects)
        self.simulator.initialize()
        self.assertEqual(self.simulator.simulate(2.5).num_events, 4)

    def make_cyclical_messaging_network_sim(self, simulator, num_objs):
        # make simulation with cyclical messaging network
        sim_objects = [CyclicalMessagesSimulationObject(obj_name(i), i, num_objs, self)
            for i in range(num_objs)]
        simulator.add_objects(sim_objects)

    def test_cyclical_messaging_network(self):
        # test event times at simulation objects; this test should succeed with any
        # natural number for num_objs and any non-negative value of time_max
        self.make_cyclical_messaging_network_sim(self.simulator, 10)
        self.simulator.initialize()
        self.assertTrue(0<self.simulator.simulate(20).num_events)

    def test_message_queues(self):
        warnings.simplefilter("ignore")
        # test with an empty event queue
        class InactiveSimulationObject(ApplicationSimulationObject):

            def __init__(self):
                SimulationObject.__init__(self, 'inactive')

            def send_initial_events(self): pass

            def get_state(self): pass

            event_handlers = []

            messages_sent = [InitMsg]

        self.make_cyclical_messaging_network_sim(self.simulator, 4)
        self.simulator.add_object(InactiveSimulationObject())
        self.simulator.initialize()
        queues = self.simulator.message_queues()
        for sim_obj_name in self.simulator.simulation_objects:
            self.assertIn(sim_obj_name, queues)

        # test with self.time initialized
        self.simulator.simulate(5)
        queues = self.simulator.message_queues()
        for sim_obj_name in self.simulator.simulation_objects:
            self.assertIn(sim_obj_name, queues)

    def test_metadata_collection(self):
        self.make_one_object_simulation()
        time_max = 5
        config_dict = dict(time_max=time_max, output_dir=self.out_dir)
        self.simulator.run(config_dict=config_dict)
        sim_metadata = SimulationMetadata.read_dataclass(self.out_dir)
        self.assertIsInstance(sim_metadata, SimulationMetadata)
        self.assertEqual(sim_metadata.simulation_config.time_max, time_max)
        self.assertGreaterEqual(sim_metadata.run.run_time, 0)

        # provide AuthorMetadata
        self.simulator.reset()
        self.make_one_object_simulation()
        output_dir=tempfile.mkdtemp(dir=self.out_dir)
        config_dict = dict(time_max=time_max, output_dir=output_dir)
        author_name = 'Joe'
        author_metadata = AuthorMetadata(name=author_name)
        self.simulator.run(config_dict=config_dict, author_metadata=author_metadata)
        sim_metadata = SimulationMetadata.read_dataclass(output_dir)
        self.assertEqual(sim_metadata.author.name, author_name)

        # no output_dir
        self.simulator.reset()
        self.make_one_object_simulation()
        self.simulator.run(5.0)
        self.assertIsInstance(self.simulator.sim_metadata, SimulationMetadata)

    ### test simulation performance ###
    def prep_simulation(self, simulation_engine, num_sim_objs):
        simulation_engine.reset()
        self.make_cyclical_messaging_network_sim(simulation_engine, num_sim_objs)
        simulation_engine.initialize()

    def suspend_logging(self, log_names, new_level=LogLevel.exception):
        # cannot use environment variable(s) to modify logging because logging2.Logger() as used
        # by LoggerConfigurator().from_dict() simply reuses existing logs whose names don't change
        # instead, modify the levels of existing logs
        # get all existing levels
        existing_levels = {}    # map from log name -> handler name -> level
        for log_name in log_names:
            existing_levels[log_name] = {}
            existing_log = LogRegister.get_logger(name=log_name)
            for handler in existing_log.handlers:
                existing_levels[log_name][handler.name] = handler.min_level
        # set levels to new level
        for log_name in log_names:
            existing_log = LogRegister.get_logger(name=log_name)
            for handler in existing_log.handlers:
                handler.min_level = new_level
        return existing_levels

    def restore_logging_levels(self, log_names, existing_levels):
        for log_name in log_names:
            existing_log = LogRegister.get_logger(name=log_name)
            for handler in existing_log.handlers:
                handler.min_level = existing_levels[log_name][handler.name]

    def test_suspend_restore_logging(self):
        debug_logs = core.get_debug_logs()

        existing_levels = self.suspend_logging(self.log_names)
        # suspended
        for log_name in self.log_names:
            fast_logger = FastLogger(debug_logs.get_log(log_name), 'debug')
            self.assertEqual(fast_logger.get_level(), LogLevel.exception)

        self.restore_logging_levels(self.log_names, existing_levels)
        level_by_logger = {}
        for logger, handler_levels in existing_levels.items():
            min_level = LogLevel.exception
            for handler, level in handler_levels.items():
                if level < min_level:
                    min_level = level
            level_by_logger[logger] = min_level

        # restored
        for log_name in self.log_names:
            fast_logger = FastLogger(debug_logs.get_log(log_name), 'debug')
            self.assertEqual(fast_logger.get_level(), level_by_logger[log_name])

    # @unittest.skip("takes 3 to 5 min.")
    def test_performance(self):
        existing_levels = self.suspend_logging(self.log_names)
        simulation_engine = SimulationEngine()
        end_sim_time = 100
        num_sim_objs = 4
        max_num_profile_objects = 300
        max_num_sim_objs = 5000
        print()
        print(f"Performance test of cyclical messaging network: end simulation time: {end_sim_time}")
        unprofiled_perf = ["\n#sim obs\t# events\trun time (s)\tevents/s".expandtabs(15)]

        while num_sim_objs < max_num_sim_objs:

            # measure execution time
            self.prep_simulation(simulation_engine, num_sim_objs)
            start_time = time.process_time()
            num_events = simulation_engine.simulate(end_sim_time).num_events
            run_time = time.process_time() - start_time
            self.assertEqual(num_sim_objs*end_sim_time, num_events)
            unprofiled_perf.append("{}\t{}\t{:8.3f}\t{:8.0f}".format(num_sim_objs, num_events,
                run_time, num_events/run_time).expandtabs(15))

            # profile
            if num_sim_objs < max_num_profile_objects:
                self.prep_simulation(simulation_engine, num_sim_objs)
                out_file = os.path.join(self.out_dir, "profile_out_{}.out".format(num_sim_objs))
                locals = {'simulation_engine': simulation_engine,
                          'end_sim_time': end_sim_time}
                cProfile.runctx('num_events = simulation_engine.simulate(end_sim_time)',
                    {}, locals, filename=out_file)
                profile = pstats.Stats(out_file)
                print(f"Profile for {num_sim_objs} simulation objects:")
                profile.strip_dirs().sort_stats('cumulative').print_stats(20)

            num_sim_objs *= 4

        self.restore_logging_levels(self.log_names, existing_levels)
        performance_log = os.path.join(os.path.dirname(__file__), 'results', 'perf_results',
                                       'de_sim_performance_log.txt')
        with open(performance_log, 'a') as perf_log:
            today = datetime.today().strftime('%Y-%m-%d')
            print(f'Performance summary on {today}', end='', file=perf_log)
            print("\n".join(unprofiled_perf), file=perf_log)
            print(file=perf_log)

        print(f'Performance summary, written to {performance_log}')
        print("\n".join(unprofiled_perf))

    def test_profiling(self):
        existing_levels = self.suspend_logging(self.log_names)
        simulation_engine = SimulationEngine()
        num_sim_objs = 20
        self.prep_simulation(simulation_engine, num_sim_objs)
        end_sim_time = 200
        expected_text =['function calls', 'Ordered by: internal time', 'filename:lineno(function)']
        sim_config_dict = dict(time_max=end_sim_time,
                               output_dir=self.out_dir,
                               profile=True)
        stats = simulation_engine.simulate(config_dict=sim_config_dict).profile_stats
        self.assertTrue(isinstance(stats, pstats.Stats))
        measurements = ''.join(open(self.measurements_pathname, 'r').readlines())
        for text in expected_text:
            self.assertIn(text, measurements)

        sim_config_dict = dict(time_max=end_sim_time,
                               profile=True)
        with CaptureOutput(relay=False) as capturer:
            stats = simulation_engine.simulate(config_dict=sim_config_dict).profile_stats
            for text in expected_text:
                self.assertIn(text, capturer.get_text())
        self.assertTrue(isinstance(stats, pstats.Stats))
        self.restore_logging_levels(self.log_names, existing_levels)

    def test_mem_use_measurement(self):
        self.make_one_object_simulation()
        time_max = 20
        config_dict = dict(time_max=time_max, output_dir=self.out_dir, object_memory_change_interval=10)
        print('\nm', f'{self.out_dir}/sim_measurements.txt')
        self.simulator.simulate(config_dict=config_dict)
        expected_text =['Memory use changes by SummaryTracker', '# objects', 'float']
        measurements = ''.join(open(self.measurements_pathname, 'r').readlines())
        for text in expected_text:
            self.assertIn(text, measurements)

        self.make_one_object_simulation()
        with CaptureOutput(relay=False) as capturer:
            config_dict = dict(time_max=time_max, object_memory_change_interval=10)
            self.simulator.simulate(config_dict=config_dict)
            for text in expected_text:
                self.assertIn(text, capturer.get_text())


class Delicate(SimulationMessage):
    'Simulation message type for testing arrival order'
    attributes = ['sender_obj_num']


class ReproducibleTestSimulationObject(ApplicationSimulationObject):
    """ This sim obj is used to test whether the simulation engine is reproducible
    """
    def __init__(self, name, obj_num, array_size):
        SimulationObject.__init__(self, name)
        self.obj_num = obj_num
        self.array_size = array_size
        self.last_time = 0
        # Delicate messages should arrive before Hello messages; count the failures
        self.delicates_before_hello = 0
        # Delicate messages should be delivered in increasing (time, obj_num) order; count the failures
        self.disordered_delicates = 0
        self.last_time_delicate_num_pair = (0, 0)

    def next_objs(self, num_objs):
        # get the next num_objs sim objs in the array
        sim_objs = []
        for obj_num in range(self.obj_num, min(self.obj_num+num_objs, self.array_size)):
            sim_objs.append(self.simulator.get_object(obj_name(obj_num)))
        return sim_objs

    def sched_events(self):
        # send InitMsg to self in 1 and Delicate(id) to self and next obj in 1, but randomize send order
        receivers_n_messages = [(self, InitMsg())]
        for sim_obj in self.next_objs(2):
            receivers_n_messages.append((sim_obj, Delicate(self.obj_num)))
        random.shuffle(receivers_n_messages)
        for receiver,message in receivers_n_messages:
            self.send_event(1, receiver, message)

    def send_initial_events(self):
        self.sched_events()

    def handle_init_msg(self, event):
        self.last_time = self.time
        self.sched_events()

    def handle_delicate_msg(self, event):
        if self.last_time < self.time:
            self.delicates_before_hello +=1
        delicate_msg = event.message
        time_delicate_num_pair = (event.event_time, delicate_msg.sender_obj_num)
        if time_delicate_num_pair <= self.last_time_delicate_num_pair:
            self.disordered_delicates += 1
        self.last_time_delicate_num_pair = time_delicate_num_pair

    # register event_handler(s) in message priority order
    event_handlers = [(InitMsg, handle_init_msg), (Delicate, handle_delicate_msg)]

    # register the message types sent
    messages_sent = [InitMsg, Delicate]


class TestSimulationReproducibility(unittest.TestCase):

    NUM_SIM_OBJS = 4
    def test_reproducibility(self):
        self.simulator = SimulationEngine()

        # comprehensive reproducibility test:
        # test whether the simulation engine deterministically delivers events to objects
        # run a simulation in which sim objects execute multiple concurrent events that contain
        # messages with different types, and messages that have the same type and different contents
        # test all types of event and message sorting
        num_sim_objs = TestSimulationReproducibility.NUM_SIM_OBJS
        for i in range(num_sim_objs):
            obj_num = i+1
            self.simulator.add_object(
                ReproducibleTestSimulationObject(obj_name(obj_num), obj_num, num_sim_objs))
        self.simulator.initialize()
        self.simulator.simulate(30)
        for sim_obj in self.simulator.get_objects():
            self.assertEqual(0, sim_obj.delicates_before_hello)
            self.assertEqual(0, sim_obj.disordered_delicates)
