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
    ' My docstring '
    msg_field_names = ['attr1', 'attr2']


class ExampleEventMessage2(de_sim.EventMessage):
    " docstring "
    pass


class ExampleEventMessage3(de_sim.EventMessage):
    " docstring "
    pass


class TestEventMessageInterface(unittest.TestCase):

    def test_utils(self):
        msg_field_names = ['arg_1', 'arg_2']
        attrs = {'__slots__': msg_field_names}
        SimMsgType = type('test', (EventMessageInterface,), attrs)
        with self.assertRaisesRegex(SimulatorError, "Constructor .*'test' expects 2 arg.*but 0 provided"):
            SimMsgType()
        vals = [1, 'a']
        t = SimMsgType(*vals)
        self.assertIn(str(vals[0]), str(t))
        self.assertIn(vals[1], str(t))
        for attr in msg_field_names:
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


class TestEventMessageMeta(unittest.TestCase):

    def test_simulation_message_meta(self):
        self.assertTrue(issubclass(ExampleEventMessage1, de_sim.EventMessage))
        with warnings.catch_warnings(record=True) as w:
            class BadEventMessage2(de_sim.EventMessage):
                msg_field_names = ['x']
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

        with self.assertRaisesRegex(SimulatorError, 'must be a list of strings'):
            class BadEventMessage1(de_sim.EventMessage):
                msg_field_names = [2.5]

        with self.assertRaisesRegex(SimulatorError, 'contains duplicates'):
            class BadEventMessage3(de_sim.EventMessage):
                msg_field_names = ['x', 'y', 'x']
