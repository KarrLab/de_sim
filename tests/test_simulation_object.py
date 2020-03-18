"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-03-26
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

import random
import re
import unittest
import warnings

from de_sim.errors import SimulatorError
from de_sim.simulation_engine import SimulationEngine
from de_sim.simulation_object import (EventQueue, SimulationObject, ApplicationSimulationObject,
                                      ApplicationSimulationObjMeta, ApplicationSimulationObjectMetadata,
                                      SimObjClassPriority)
from de_sim.testing.example_simulation_objects import (ALL_MESSAGE_TYPES, TEST_SIM_OBJ_STATE,
                                                       ExampleSimulationObject,
                                                       ImproperlyRegisteredSimulationObject)
from de_sim.testing.some_message_types import InitMsg, Eg1, MsgWithAttrs, UnregisteredMsg
from wc_utils.util.list import is_sorted
from wc_utils.util.misc import most_qual_cls_name

EVENT_HANDLERS = ApplicationSimulationObjMeta.EVENT_HANDLERS
MESSAGES_SENT = ApplicationSimulationObjMeta.MESSAGES_SENT
CLASS_PRIORITY = ApplicationSimulationObjMeta.CLASS_PRIORITY


class TestEventQueue(unittest.TestCase):

    def setUp(self):
        self.event_queue = EventQueue()
        self.num_events = 5
        self.sender = sender = ExampleSimulationObject('sender')
        self.receiver = receiver = ExampleSimulationObject('receiver')
        for i in range(self.num_events):
            self.event_queue.schedule_event(i, i+1, sender, receiver, InitMsg())

    def test_reset(self):
        self.event_queue.reset()
        self.assertEqual(float('inf'), self.event_queue.next_event_time())
        self.assertTrue(self.event_queue.empty())
        self.assertFalse(self.event_queue.next_events())

    def test_next_event_time(self):
        empty_event_queue = EventQueue()
        self.assertEqual(float('inf'), empty_event_queue.next_event_time())
        self.assertEqual(1, self.event_queue.next_event_time())

    def test_next_event_obj(self):
        self.assertEqual(self.receiver, self.event_queue.next_event_obj())
        self.event_queue.reset()
        self.assertEqual(None, self.event_queue.next_event_obj())

    def test_simple_next_events(self):
        next_events = self.event_queue.next_events()
        self.assertEqual(len(next_events), 1)
        event = next_events[0]
        self.assertEqual(event.event_time, 1)
        self.assertEqual(event.receiving_object, self.receiver)
        self.assertEqual(type(event.message), InitMsg)
        for i in range(self.num_events):
            next_events = self.event_queue.next_events()

    def test_concurrent_events(self):
        # identical concurrent events to one object
        self.event_queue.reset()
        self.event_queue.schedule_event(0, 1, self.sender, self.receiver, InitMsg())
        self.event_queue.schedule_event(0, 1, self.sender, self.receiver, InitMsg())
        self.assertEqual(1, self.event_queue.next_event_time())
        self.assertEqual(self.receiver, self.event_queue.next_event_obj())
        next_events = self.event_queue.next_events()
        self.assertEqual(len(next_events), 2)
        for event in next_events:
            self.assertEqual(event.event_time, 1)
            self.assertEqual(event.receiving_object, self.receiver)
            self.assertEqual(type(event.message), InitMsg)

        # concurrent events to multiple objects
        self.receiver2 = ExampleSimulationObject('receiver2')
        self.event_queue.schedule_event(0, 1, self.sender, self.receiver, InitMsg())
        self.event_queue.schedule_event(0, 1, self.sender, self.receiver2, InitMsg())
        self.event_queue.schedule_event(0, 1, self.sender, self.receiver2, InitMsg())
        self.event_queue.schedule_event(0, 1, self.sender, self.receiver, InitMsg())
        self.event_queue.schedule_event(0, 1, self.sender, self.receiver2, InitMsg())

        # get 2 events for receiver
        self.assertEqual(1, self.event_queue.next_event_time())
        self.assertEqual(self.receiver, self.event_queue.next_event_obj())
        next_events = self.event_queue.next_events()
        self.assertEqual(len(next_events), 2)
        for event in next_events:
            self.assertEqual(event.receiving_object, self.receiver)

        # get 3 events for receiver2
        self.assertEqual(1, self.event_queue.next_event_time())
        self.assertEqual(self.receiver2, self.event_queue.next_event_obj())
        next_events = self.event_queue.next_events()
        self.assertEqual(len(next_events), 3)
        for event in next_events:
            self.assertEqual(event.receiving_object, self.receiver2)

    def test_exceptions(self):
        eq = EventQueue()

        st, rt = 2, 1
        with self.assertRaisesRegex(SimulatorError,
            re.escape("receive_time < send_time in schedule_event(): {} < {}".format(rt, st))):
            eq.schedule_event(st, rt , None, None, '')

        with self.assertRaisesRegex(SimulatorError,
            'message should be an instance of SimulationMessage but is a'):
            eq.schedule_event(1, 2, None, None, 13)

        with self.assertRaisesRegex(SimulatorError, 'send_time .* and/or receive_time .* is NaN'):
            eq.schedule_event(float('NaN'), 1, None, None, '')
        with self.assertRaisesRegex(SimulatorError, 'send_time .* and/or receive_time .* is NaN'):
            eq.schedule_event(1, float('NaN'), None, None, '')

    def test_render(self):
        self.assertEqual(None, EventQueue().render())
        self.assertEqual('', str(EventQueue()))
        self.assertEqual(self.event_queue.render(), str(self.event_queue))
        self.assertEqual(len(self.event_queue.render(as_list=True)), self.num_events+1)
        def get_event_times(eq_rendered_as_list):
            return [row[1] for row in eq_rendered_as_list[1:]]
        self.assertTrue(is_sorted(get_event_times(self.event_queue.render(as_list=True))))

        # test sorting
        test_eq = EventQueue()
        num_events = 10
        for i in range(num_events):
            test_eq.schedule_event(i, random.uniform(i, i+num_events), self.sender, self.receiver,
                MsgWithAttrs(2, 3))
        self.assertTrue(is_sorted(get_event_times(test_eq.render(as_list=True))))

        # test multiple message types
        test_eq = EventQueue()
        num_events = 20
        for i in range(num_events):
            msg = random.choice([InitMsg(), MsgWithAttrs(2, 3)])
            test_eq.schedule_event(i, i+1, self.sender, self.receiver, msg)
        self.assertEqual(len(test_eq.render(as_list=True)), num_events+1)
        self.assertTrue(is_sorted(get_event_times(test_eq.render(as_list=True))))
        for attr in MsgWithAttrs.__slots__:
            self.assertIn("\t{}:".format(attr), test_eq.render())

    def test_filtered_render(self):
        # test multiple receivers and filtered by receiver
        receiver2 = ExampleSimulationObject('receiver2')
        start, end = 3, 5
        times = range(start, end)
        for time in times:
            self.event_queue.schedule_event(0, time, self.sender, receiver2, InitMsg())
        self.assertEqual(len(self.event_queue.render(sim_obj=self.receiver, as_list=True)),
            self.num_events+1)
        self.assertEqual(len(self.event_queue.render(sim_obj=receiver2, as_list=True)), len(times)+1)


class ASOwithoutEventHandlers(ExampleSimulationObject):
    # register the message types sent
    messages_sent = [MsgWithAttrs]


class ASOwithoutMessagesSent(ExampleSimulationObject):
    def handler(self, event): pass
    event_handlers = [(InitMsg, 'handler')]


class ASOwithDefaultClassPriority(ApplicationSimulationObject):
    def handler(self, event): pass
    event_handlers = [(InitMsg, 'handler')]


class TestApplicationSimulationObjMeta(unittest.TestCase):

    def test_correct_code(self):
        warnings.simplefilter("ignore")

        # test short circuit
        self.assertFalse(hasattr(ApplicationSimulationObject, 'metadata'))

        # test metadata presence
        self.assertTrue(hasattr(ASOwithoutEventHandlers, 'metadata'))
        self.assertTrue(isinstance(getattr(ASOwithoutEventHandlers, 'metadata'), ApplicationSimulationObjectMetadata))

        # test abstract
        class AbstractASO(ApplicationSimulationObject):
            abstract = True
        metadata = AbstractASO.metadata
        self.assertFalse(metadata.event_handlers_dict)
        self.assertFalse(metadata.message_types_sent)

        # test correct event_handlers and messages_sent declarations in an ApplicationSimulationObject
        ExampleSimObj = ExampleSimulationObject
        self.assertTrue(isinstance(getattr(ExampleSimObj, 'metadata'), ApplicationSimulationObjectMetadata))
        metadata = ExampleSimObj.metadata
        expected_event_handlers = {InitMsg:ExampleSimObj.handler, Eg1:ExampleSimObj.handler}
        self.assertEqual(metadata.event_handlers_dict, expected_event_handlers)
        event_handler_priorities = metadata.event_handler_priorities
        self.assertTrue(metadata.event_handler_priorities[InitMsg] < metadata.event_handler_priorities[Eg1])
        self.assertEqual(metadata.event_handler_priorities[InitMsg], 0)
        self.assertEqual(metadata.message_types_sent, set(ALL_MESSAGE_TYPES))

        # test no messages_sent
        class ChildOfASOwithoutMessagesSent(ApplicationSimulationObject):
            def handler(self, event): pass
            event_handlers = [(InitMsg, 'handler')]
        metadata = ChildOfASOwithoutMessagesSent.metadata
        self.assertEqual(metadata.message_types_sent, set())

        # test inherited event_handlers
        metadata = ASOwithoutEventHandlers.metadata
        self.assertEqual(metadata.event_handlers_dict, expected_event_handlers)

        # test inherited messages_sent
        metadata = ASOwithoutMessagesSent.metadata
        self.assertEqual(metadata.message_types_sent, set(ALL_MESSAGE_TYPES))

        # test class_priority
        self.assertEqual(ExampleSimObj.class_priority, SimObjClassPriority.HIGH)

        # test default class_priority
        self.assertEqual(ASOwithDefaultClassPriority.metadata.class_priority, SimObjClassPriority.LOW)
        sim_obj_a = ASOwithDefaultClassPriority('a')
        self.assertEqual(sim_obj_a.class_event_priority, SimObjClassPriority.LOW)

        # test inherited class_priority
        self.assertEqual(ASOwithoutEventHandlers.class_priority, SimObjClassPriority.HIGH)

    def test_errors(self):
        warnings.simplefilter("ignore")

        # missing event_handlers and messages_sent
        expected_error = "ApplicationSimulationObject.*definition must inherit or provide a non-empty '{}' or '{}'".format(
                EVENT_HANDLERS, MESSAGES_SENT)
        with self.assertRaisesRegex(SimulatorError, expected_error):
            class EmptyASO(ApplicationSimulationObject): pass
        with self.assertRaisesRegex(SimulatorError, expected_error):
            class BadASO1(ApplicationSimulationObject): event_handlers = []
        with self.assertRaisesRegex(SimulatorError, expected_error):
            class BadASO2(ApplicationSimulationObject): messages_sent = []

        # no such handler
        with self.assertRaises(SimulatorError):
            class BadASO3(ApplicationSimulationObject): event_handlers = [(InitMsg, 'no_such_handler')]

        # handler not callable
        with self.assertRaises(SimulatorError):
            class BadASO4(ApplicationSimulationObject):
                handler_not_callable = 2
                event_handlers = [(InitMsg, 'handler_not_callable')]

        with self.assertRaises(SimulatorError):
            class BadASO4_2(ApplicationSimulationObject):
                handler_not_callable = 'string_not_callable'
                event_handlers = [(InitMsg, 'handler_not_callable')]

        # message must be a subclass of SimulationMessage
        class Obj(object): pass
        with self.assertRaises(SimulatorError):
            class BadASO5(ApplicationSimulationObject):
                def handler(self, event): pass
                event_handlers = [(Obj, 'handler')]

        # event_handlers isn't iterable over pairs
        with self.assertRaises(SimulatorError):
            class BadASO6(ApplicationSimulationObject):
                def handler(self, event): pass
                event_handlers = (InitMsg, 'handler')

        # message in messages_sent must be a subclass of SimulationMessage
        with self.assertRaises(SimulatorError):
            class BadASO7(ApplicationSimulationObject):
                messages_sent = [Obj]

        # messages_sent isn't iterable
        with self.assertRaises(SimulatorError):
            class BadASO8(ApplicationSimulationObject):
                messages_sent = Obj

        # message type repeated
        with self.assertRaises(SimulatorError):
            class BadASO9(ApplicationSimulationObject):
                def handler(self, event): pass
                event_handlers = [(InitMsg, 'handler'), (InitMsg, 'handler')]

        # class priority not an int
        with self.assertRaises(SimulatorError):
            class ASOwithWrongClassPriorityType(ExampleSimulationObject):
                messages_sent = [MsgWithAttrs]
                class_priority = 'x'

    def test_warnings(self):

        # missing event_handlers
        with warnings.catch_warnings(record=True) as w:
            class PartlyRegisteredSimulationObject1(ApplicationSimulationObject):
                messages_sent = [InitMsg]
            self.assertEqual(str(w[-1].message),
                "ApplicationSimulationObject 'PartlyRegisteredSimulationObject1' definition does not inherit "
                    "or provide a non-empty '{}'.".format(EVENT_HANDLERS))
            self.assertTrue(InitMsg in PartlyRegisteredSimulationObject1.metadata.message_types_sent)
            self.assertFalse(PartlyRegisteredSimulationObject1.metadata.event_handlers_dict)

        # missing messages_sent
        with warnings.catch_warnings(record=True) as w:
            class PartlyRegisteredSimulationObject2(ApplicationSimulationObject):
                event_handlers = [(InitMsg, 'handler')]
                def handler(self): pass
            self.assertEqual(str(w[-1].message),
                "ApplicationSimulationObject 'PartlyRegisteredSimulationObject2' definition does not inherit "
                    "or provide a non-empty '{}'.".format(MESSAGES_SENT))
            self.assertTrue(InitMsg in PartlyRegisteredSimulationObject2.metadata.event_handlers_dict)
            self.assertEqual(PartlyRegisteredSimulationObject2.metadata.event_handlers_dict[InitMsg],
                PartlyRegisteredSimulationObject2.handler)


class TestSimObjClassPriority(unittest.TestCase):

    def test(self):
        o = SimObjClassPriority.HIGH
        self.assertIn('HIGH', str(o))

    def test_assign_decreasing_priority(self):

        class ASOwithNoClassPriority_1(ExampleSimulationObject):
            messages_sent = [MsgWithAttrs]

        class ASOwithNoClassPriority_2(ExampleSimulationObject):
            messages_sent = [MsgWithAttrs]

        SimObjClassPriority.assign_decreasing_priority([ASOwithNoClassPriority_1,
                                                        ASOwithNoClassPriority_2])
        self.assertEqual(ASOwithNoClassPriority_1.metadata.class_priority, 1)
        self.assertEqual(ASOwithNoClassPriority_2.metadata.class_priority, 2)

        with self.assertRaises(SimulatorError):
            SimObjClassPriority.assign_decreasing_priority(range(SimObjClassPriority.LOW + 1))


class TestApplicationSimulationObject(unittest.TestCase):

    def test_set_class_priority(self):

        class ASOwithMediumClassPriority(ApplicationSimulationObject):
            def handler(self, event): pass
            event_handlers = [(InitMsg, 'handler')]

            # set MEDIUM priority
            class_priority = SimObjClassPriority.MEDIUM

        test_aso_1 = ASOwithMediumClassPriority('name')
        self.assertEqual(test_aso_1.metadata.class_priority, SimObjClassPriority.MEDIUM)
        test_aso_1.set_class_priority(SimObjClassPriority.HIGH)
        self.assertEqual(test_aso_1.metadata.class_priority, SimObjClassPriority.HIGH)


class TestSimulationObject(unittest.TestCase):

    def setUp(self):
        self.good_name = 'arthur'
        self.eso1 = ExampleSimulationObject(self.good_name)
        self.irso1 = ImproperlyRegisteredSimulationObject(self.good_name)
        self.simulator = SimulationEngine()
        self.o1 = ExampleSimulationObject('o1')
        self.o2 = ExampleSimulationObject('o2')
        self.simulator.add_objects([self.o1, self.o2])
        self.simulator.initialize()

    def test_attributes(self):
        self.assertEqual(self.good_name, self.eso1.name)
        self.assertEqual(0, self.eso1.time)
        self.assertEqual(0, self.eso1.num_events)
        self.assertEqual(None, self.eso1.simulator)

    def test_exceptions(self):
        expected = "'{}' simulation objects not registered to send '{}' messages".format(
            most_qual_cls_name(self.eso1), UnregisteredMsg().__class__.__name__)
        with self.assertRaisesRegex(SimulatorError, expected):
            self.eso1.send_event_absolute(2, self.eso1, UnregisteredMsg())

        expected = "'{}' simulation objects not registered to receive '{}' messages".format(
            most_qual_cls_name(self.irso1), InitMsg().__class__.__name__)
        with self.assertRaisesRegex(SimulatorError, expected):
            self.eso1.send_event_absolute(2, self.irso1, InitMsg())

        with self.assertRaisesRegex(SimulatorError,
            "simulation messages must be instances of type 'SimulationMessage'; "):
            self.eso1.send_event_absolute(2, self.irso1, InitMsg)

        with self.assertRaisesRegex(SimulatorError, "event_time is 'NaN'"):
            self.eso1.send_event_absolute(float('NaN'), self.eso1, UnregisteredMsg())

    def test_get_receiving_priorities_dict(self):
        self.assertTrue(ExampleSimulationObject.metadata.event_handler_priorities[InitMsg] <
            ExampleSimulationObject.metadata.event_handler_priorities[Eg1])
        receiving_priorities = self.eso1.get_receiving_priorities_dict()
        self.assertTrue(receiving_priorities[InitMsg] < receiving_priorities[Eg1])

    def test_send_events(self):
        times=[2.0, 1.0, 0.5]
        # test both send_event methods
        for copy in [False, True]:
            for send_method in [self.o1.send_event, self.o1.send_event_absolute]:

                for t in times:
                    send_method(t, self.o2, Eg1(), copy=copy)

                tmp = sorted(times)
                while self.o2.simulator.event_queue.next_event_time() < float('inf'):
                    self.assertEqual(self.o2.simulator.event_queue.next_event_time(), tmp.pop(0))
                    self.o2.simulator.event_queue.next_events()
                self.assertEqual(self.o2.simulator.event_queue.next_events(), [])

    def test_simultaneous_event_times(self):
        self.o1.send_event(0, self.o2, Eg1())
        self.o1.send_event(2, self.o2, InitMsg())

        num=20
        self.o1.send_event(1, self.o2, InitMsg())
        for i in range(num):
            if random.choice([True, False]):
                self.o1.send_event(1, self.o2, Eg1())
            else:
                self.o1.send_event(1, self.o2, InitMsg())

        self.assertEqual(self.simulator.event_queue.next_event_time(), 0)
        event_list = self.simulator.event_queue.next_events()
        self.assertEqual(event_list[0].event_time, 0)

        self.assertEqual(self.simulator.event_queue.next_event_time(), 1)
        event_list = self.simulator.event_queue.next_events()
        # all InitMsg messages come before any Eg1 message,
        # and at least 1 InitMsg message exists
        expected_type = InitMsg
        switched = False
        for event in event_list:
            if not switched and event.message.__class__ == Eg1:
                expected_type = Eg1
            self.assertEqual(event.message.__class__, expected_type)

        self.assertEqual(self.simulator.event_queue.next_event_time(), 2)

        # use event_time_tiebreaker to order simultaneous events earlier at o3
        def tiebreaker_first_event(simulator):
            event_list = simulator.event_queue.next_events()
            return event_list[0]._get_order_time()[-1]

        o3_event_time_tiebreaker = 'a'
        options = dict(event_time_tiebreaker=o3_event_time_tiebreaker)
        o3 = ExampleSimulationObject('o3', **options)
        self.o1.send_event(1, o3, Eg1())
        self.o1.send_event(1, self.o2, Eg1())
        self.assertEqual(tiebreaker_first_event(self.simulator), o3_event_time_tiebreaker)
        self.assertEqual(tiebreaker_first_event(self.simulator), self.o2.name)

    def test_render_event_queue(self):
        rv = self.o1.render_event_queue()

        times=[2.0, 1.0, 0.5]
        for time in times:
            self.o1.send_event(time, self.o1, Eg1())
        rv = self.o1.render_event_queue()
        self.assertIn(self.o1.name, rv)
        # 1 extra row for the header
        self.assertEqual(len(rv.split('\n')), len(times)+1)
        for time in times:
            self.assertIn(str(time), rv)

    def test_event_exceptions(self):
        delay = -1.0
        with self.assertRaisesRegex(SimulatorError,
            re.escape("delay < 0 in send_event(): {}".format(delay))):
            self.o1.send_event(delay, self.o2, Eg1())

        event_time = -1
        with self.assertRaisesRegex(SimulatorError,
            r'event_time \(-1.*\) < current time \(0.*\) in send_event_absolute\(\)'):
            self.o1.send_event_absolute(event_time, self.o2, Eg1())

        with self.assertRaisesRegex(SimulatorError,
            "SimulationObject '{}' is already part of a simulator".format(self.o1.name)):
            self.o1.add(self.simulator)

        with self.assertRaisesRegex(SimulatorError, "delay is 'NaN'"):
            self.o1.send_event(float('nan'), self.o2, Eg1())

    def test_misc(self):
        self.assertEqual(self.o1.get_state(), TEST_SIM_OBJ_STATE)
