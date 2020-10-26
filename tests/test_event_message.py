"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-06-01
:Copyright: 2017-2020, Karr Lab
:License: MIT
"""

import unittest
import warnings

from de_sim.event_message import EventMessageInterface
from de_sim.errors import SimulatorError
from wc_utils.util.list import elements_to_str
import de_sim


class ExampleEventMessage1(de_sim.EventMessage):
    "My docstring"
    attr1: str
    attr2: int


class ExampleEventMessage2(de_sim.EventMessage):
    "Docstring"
    pass


class ExampleEventMessage3(de_sim.EventMessage):
    "Docstring"


class TestEventMessageInterface(unittest.TestCase):

    def test_utils(self):
        attributes = ['arg_1', 'arg_2']
        attrs = {'__slots__': attributes}
        SimMsgType = type('test', (EventMessageInterface,), attrs)
        with self.assertRaisesRegex(SimulatorError, "Constructor .*'test' expects 2 arg.*but 0 provided"):
            SimMsgType()
        vals = [1, 'a']
        t = SimMsgType(*vals)
        self.assertIn(str(vals[0]), str(t))
        self.assertIn(vals[1], str(t))
        for attr in attributes:
            self.assertIn(attr, t.attrs())
            self.assertIn(attr, t.header())
            self.assertIn(attr, t.header(as_list=True))
            self.assertIn(attr, t.values(annotated=True))
            self.assertIn(attr, t.values(annotated=True, separator=','))
        self.assertEqual(elements_to_str(vals), t.values(as_list=True))
        self.assertEqual('\t'.join(elements_to_str(vals)), t.values())
        delattr(t, 'arg_2')
        self.assertIn(str(None), str(t))
        self.assertEqual([1, None], t._values())

    def test_simple_msg(self):
        sim_msg_2 = ExampleEventMessage2()
        self.assertEqual(None, sim_msg_2.values())

    def comparison(self, lesser, greater):
        self.assertTrue(lesser < greater)
        self.assertFalse(lesser > greater)
        self.assertTrue(lesser <= greater)
        self.assertTrue(greater > lesser)
        self.assertFalse(greater < lesser)
        self.assertTrue(greater >= lesser)

    def test_comparison(self):
        # test messages with no message fields
        sim_msg_2 = ExampleEventMessage2()
        self.assertTrue(sim_msg_2 <= sim_msg_2)
        self.assertTrue(sim_msg_2 >= sim_msg_2)
        sim_msg_3 = ExampleEventMessage3()
        self.comparison(sim_msg_2, sim_msg_3)

        # test messages with message fields
        attrsa = (1, 'bye')
        sim_msg_1a = ExampleEventMessage1(*attrsa)
        self.assertTrue(sim_msg_1a <= sim_msg_1a)
        self.assertTrue(sim_msg_1a >= sim_msg_1a)
        attrsb = (1, 'hi')
        sim_msg_1b = ExampleEventMessage1(*attrsb)
        self.comparison(sim_msg_1a, sim_msg_1b)

        # test messages with message fields that cannot be compared
        sim_msg_1_bad_a = ExampleEventMessage1(str, str)
        sim_msg_1_bad_b = ExampleEventMessage1(int, int)
        with self.assertRaises(TypeError):
            sim_msg_1_bad_a < sim_msg_1_bad_b

    def test_metadata(self):

        class ExampleEventMessage(de_sim.EventMessage):
            'My docstring'
            unit_price: float
            name: str = 'hi'
            quantity_on_hand: int = 0

        eem = ExampleEventMessage(2.2, 'bye', 3)
        self.assertEqual(eem._default_values, dict(name='hi', quantity_on_hand=0))
        self.assertEqual(eem._annotations, dict(unit_price=float,
                                                name=str,
                                                quantity_on_hand=int))


class TestEventMessageMeta(unittest.TestCase):

    def test_simulation_message_meta(self):

        self.assertTrue(issubclass(ExampleEventMessage1, de_sim.EventMessage))
        with warnings.catch_warnings(record=True) as w:
            class IncompleteEventMessage(de_sim.EventMessage):
                x: float
            self.assertIn("definition does not contain a docstring", str(w[-1].message))
        warnings.simplefilter("ignore")

        self.assertEqual(ExampleEventMessage1.__doc__, 'My docstring')
        attr_vals = ('att1_val', 'att2_val')
        example_simulation_message = ExampleEventMessage1(*attr_vals)
        attrs = ['attr1', 'attr2']
        for attr, val in zip(attrs, attr_vals):
            self.assertEqual(getattr(example_simulation_message, attr), val)

        example_simulation_message2 = ExampleEventMessage2()
        self.assertEqual(example_simulation_message2.attrs(), [])
        self.assertEqual(example_simulation_message2.header(), None)

        with self.assertRaisesRegex(SimulatorError, 'Wrong type of default value'):
            class EventMessageBadTypes(de_sim.EventMessage):
                "Docstring"
                unit_price: float = 'x'
                quantity_on_hand: str = 3

        with self.assertRaisesRegex(SimulatorError, 'Optional attributes must follow required attributes'):
            class EventMessageRequiredAfterOptional(de_sim.EventMessage):
                "Docstring"
                unit_price: float = 10.0
                quantity_on_hand: int
