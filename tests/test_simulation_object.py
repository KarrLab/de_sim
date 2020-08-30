"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-03-26
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

import random
import re
import unittest
import warnings

from de_sim.errors import SimulatorError
from de_sim.simulation_object import (SimulationObject, SimulationObjMeta, SimulationObjectMetadata,
                                      SimObjClassPriority)
from de_sim.testing.example_simulation_objects import (ALL_MESSAGE_TYPES, ExampleSimulationObject,
                                                       ImproperlyRegisteredSimulationObject)
from de_sim.testing.some_message_types import InitMsg, Eg1, MsgWithAttrs, UnregisteredMsg
from wc_utils.util.misc import most_qual_cls_name
import de_sim

EVENT_HANDLERS = SimulationObjMeta.EVENT_HANDLERS
MESSAGES_SENT = SimulationObjMeta.MESSAGES_SENT
CLASS_PRIORITY = SimulationObjMeta.CLASS_PRIORITY


class SOwithoutEventHandlers(ExampleSimulationObject):
    # register the message types sent
    messages_sent = [MsgWithAttrs]


class SOwithoutMessagesSent(ExampleSimulationObject):
    def handler(self, event):
        pass
    event_handlers = [(InitMsg, 'handler')]


class SOwithDefaultClassPriority(SimulationObject):
    def handler(self, event):
        pass
    event_handlers = [(InitMsg, 'handler')]


class TestSimulationObjMeta(unittest.TestCase):

    def test_correct_code(self):
        warnings.simplefilter("ignore")

        # test short circuit
        self.assertFalse(hasattr(SimulationObject, 'metadata'))

        # test metadata presence
        self.assertTrue(hasattr(SOwithoutEventHandlers, 'metadata'))
        self.assertTrue(isinstance(getattr(SOwithoutEventHandlers, 'metadata'), SimulationObjectMetadata))

        # test abstract
        class AbstractSO(SimulationObject):
            abstract = True
        metadata = AbstractSO.metadata
        self.assertFalse(metadata.event_handlers_dict)
        self.assertFalse(metadata.message_types_sent)

        # test correct event_handlers and messages_sent declarations in an SimulationObject
        ExampleSimObj = ExampleSimulationObject
        self.assertTrue(isinstance(getattr(ExampleSimObj, 'metadata'), SimulationObjectMetadata))
        metadata = ExampleSimObj.metadata
        expected_event_handlers = {InitMsg: ExampleSimObj.handler, Eg1: ExampleSimObj.handler}
        self.assertEqual(metadata.event_handlers_dict, expected_event_handlers)
        event_handler_priorities = metadata.event_handler_priorities
        self.assertTrue(event_handler_priorities[InitMsg] < event_handler_priorities[Eg1])
        self.assertEqual(event_handler_priorities[InitMsg], 0)
        self.assertEqual(metadata.message_types_sent, set(ALL_MESSAGE_TYPES))

        # test no messages_sent
        class ChildOfSOwithoutMessagesSent(SimulationObject):
            def handler(self, event):
                pass
            event_handlers = [(InitMsg, 'handler')]
        metadata = ChildOfSOwithoutMessagesSent.metadata
        self.assertEqual(metadata.message_types_sent, set())

        # test inherited event_handlers
        metadata = SOwithoutEventHandlers.metadata
        self.assertEqual(metadata.event_handlers_dict, expected_event_handlers)

        # test inherited messages_sent
        metadata = SOwithoutMessagesSent.metadata
        self.assertEqual(metadata.message_types_sent, set(ALL_MESSAGE_TYPES))

        # test class_priority
        self.assertEqual(ExampleSimObj.class_priority, SimObjClassPriority.HIGH)

        # test default class_priority
        self.assertEqual(SOwithDefaultClassPriority.metadata.class_priority, SimObjClassPriority.LOW)
        sim_obj_a = SOwithDefaultClassPriority('a')
        self.assertEqual(sim_obj_a.class_event_priority, SimObjClassPriority.LOW)

        # test inherited class_priority
        self.assertEqual(SOwithoutEventHandlers.class_priority, SimObjClassPriority.HIGH)

    def test_errors(self):
        warnings.simplefilter("ignore")

        # missing event_handlers and messages_sent
        expected_error = "SimulationObject.*definition must inherit or provide a non-empty '{}' or '{}'".format(
            EVENT_HANDLERS, MESSAGES_SENT)
        with self.assertRaisesRegex(SimulatorError, expected_error):
            class EmptySO(SimulationObject):
                pass
        with self.assertRaisesRegex(SimulatorError, expected_error):
            class BadSO1(SimulationObject):
                event_handlers = []
        with self.assertRaisesRegex(SimulatorError, expected_error):
            class BadSO2(SimulationObject):
                messages_sent = []

        # no such handler
        with self.assertRaises(SimulatorError):
            class BadSO3(SimulationObject):
                event_handlers = [(InitMsg, 'no_such_handler')]

        # handler not callable
        with self.assertRaises(SimulatorError):
            class BadSO4(SimulationObject):
                handler_not_callable = 2
                event_handlers = [(InitMsg, 'handler_not_callable')]

        with self.assertRaises(SimulatorError):
            class BadSO4_2(SimulationObject):
                handler_not_callable = 'string_not_callable'
                event_handlers = [(InitMsg, 'handler_not_callable')]

        # message must be a subclass of EventMessage
        class Obj(object):
            pass
        with self.assertRaises(SimulatorError):
            class BadSO5(SimulationObject):
                def handler(self, event):
                    pass
                event_handlers = [(Obj, 'handler')]

        # event_handlers isn't iterable over pairs
        with self.assertRaises(SimulatorError):
            class BadSO6(SimulationObject):
                def handler(self, event):
                    pass
                event_handlers = (InitMsg, 'handler')

        # message in messages_sent must be a subclass of EventMessage
        with self.assertRaises(SimulatorError):
            class BadSO7(SimulationObject):
                messages_sent = [Obj]

        # messages_sent isn't iterable
        with self.assertRaises(SimulatorError):
            class BadSO8(SimulationObject):
                messages_sent = Obj

        # message type repeated
        with self.assertRaises(SimulatorError):
            class BadSO9(SimulationObject):
                def handler(self, event):
                    pass
                event_handlers = [(InitMsg, 'handler'), (InitMsg, 'handler')]

        # class priority not an int
        with self.assertRaises(SimulatorError):
            class SOwithWrongClassPriorityType(ExampleSimulationObject):
                messages_sent = [MsgWithAttrs]
                class_priority = 'x'

    def test_warnings(self):

        # missing event_handlers
        with warnings.catch_warnings(record=True) as w:
            class PartlyRegisteredSimulationObject1(SimulationObject):
                messages_sent = [InitMsg]
            self.assertEqual(str(w[-1].message),
                             "SimulationObject 'PartlyRegisteredSimulationObject1' definition does not inherit "
                             "or provide a non-empty '{}'.".format(EVENT_HANDLERS))
            self.assertTrue(InitMsg in PartlyRegisteredSimulationObject1.metadata.message_types_sent)
            self.assertFalse(PartlyRegisteredSimulationObject1.metadata.event_handlers_dict)

        # missing messages_sent
        with warnings.catch_warnings(record=True) as w:
            class PartlyRegisteredSimulationObject2(SimulationObject):
                event_handlers = [(InitMsg, 'handler')]

                def handler(self):
                    pass
            self.assertEqual(str(w[-1].message),
                             "SimulationObject 'PartlyRegisteredSimulationObject2' definition does not inherit "
                             "or provide a non-empty '{}'.".format(MESSAGES_SENT))
            self.assertTrue(InitMsg in PartlyRegisteredSimulationObject2.metadata.event_handlers_dict)
            self.assertEqual(PartlyRegisteredSimulationObject2.metadata.event_handlers_dict[InitMsg],
                             PartlyRegisteredSimulationObject2.handler)


class TestSimObjClassPriority(unittest.TestCase):

    def test(self):
        o = SimObjClassPriority.HIGH
        self.assertIn('HIGH', str(o))

    def test_assign_decreasing_priority(self):

        class SOwithNoClassPriority_1(ExampleSimulationObject):
            messages_sent = [MsgWithAttrs]

        class SOwithNoClassPriority_2(ExampleSimulationObject):
            messages_sent = [MsgWithAttrs]

        SimObjClassPriority.assign_decreasing_priority([SOwithNoClassPriority_1,
                                                        SOwithNoClassPriority_2])
        self.assertEqual(SOwithNoClassPriority_1.metadata.class_priority, 1)
        self.assertEqual(SOwithNoClassPriority_2.metadata.class_priority, 2)

        with self.assertRaises(SimulatorError):
            SimObjClassPriority.assign_decreasing_priority(range(SimObjClassPriority.LOW + 1))


class TestSimulationObjectPriority(unittest.TestCase):

    def test_set_class_priority(self):

        class SOwithMediumClassPriority(SimulationObject):
            def handler(self, event):
                pass
            event_handlers = [(InitMsg, 'handler')]

            # set MEDIUM priority
            class_priority = SimObjClassPriority.MEDIUM

        test_so_1 = SOwithMediumClassPriority('name')
        self.assertEqual(test_so_1.metadata.class_priority, SimObjClassPriority.MEDIUM)
        test_so_1.set_class_priority(SimObjClassPriority.HIGH)
        self.assertEqual(test_so_1.metadata.class_priority, SimObjClassPriority.HIGH)


class TestSimulationObject(unittest.TestCase):

    def setUp(self):
        self.good_name = 'arthur'
        self.eso1 = ExampleSimulationObject(self.good_name)
        self.irso1 = ImproperlyRegisteredSimulationObject(self.good_name)
        self.simulator = de_sim.Simulator()
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
                                    "event messages must be instances of type 'EventMessage'; "):
            self.eso1.send_event_absolute(2, self.irso1, InitMsg)

        with self.assertRaisesRegex(SimulatorError, "event_time is 'NaN'"):
            self.eso1.send_event_absolute(float('NaN'), self.eso1, UnregisteredMsg())

    def test_get_receiving_priorities_dict(self):
        self.assertTrue(ExampleSimulationObject.metadata.event_handler_priorities[InitMsg] <
                        ExampleSimulationObject.metadata.event_handler_priorities[Eg1])
        receiving_priorities = self.eso1.get_receiving_priorities_dict()
        self.assertTrue(receiving_priorities[InitMsg] < receiving_priorities[Eg1])

    def test_send_events(self):
        times = [2.0, 1.0, 0.5]
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

        num = 20
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
