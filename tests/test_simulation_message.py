"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-06-01
:Copyright: 2017-2020, Karr Lab
:License: MIT
"""

import unittest
import warnings

from de_sim.simulation_message import SimulationMessage, SimulationMessageInterface
from de_sim.errors import SimulatorError
from wc_utils.util.list import elements_to_str


class ExampleSimulationMessage1(SimulationMessage):
    ' My docstring '
    attributes = ['attr1', 'attr2']


class ExampleSimulationMessage2(SimulationMessage):
    " docstring "
    pass


class ExampleSimulationMessage3(SimulationMessage):
    " docstring "
    pass


class TestSimulationMessageInterface(unittest.TestCase):

    def test_utils(self):
        attributes = ['arg_1','arg_2']
        attrs = {'__slots__':attributes}
        SimMsgType = type('test', (SimulationMessageInterface,), attrs)
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
        sim_msg_2 = ExampleSimulationMessage2()
        self.assertEqual(None, sim_msg_2.values())

    def comparison(self, lesser, greater):
        self.assertTrue(lesser < greater)
        self.assertFalse(lesser > greater)
        self.assertTrue(lesser <= greater)
        self.assertTrue(greater > lesser)
        self.assertFalse(greater < lesser)
        self.assertTrue(greater >= lesser)

    def test_comparison(self):
        # test messages with no attributes
        sim_msg_2 = ExampleSimulationMessage2()
        self.assertTrue(sim_msg_2 <= sim_msg_2)
        self.assertTrue(sim_msg_2 >= sim_msg_2)
        sim_msg_3 = ExampleSimulationMessage3()
        self.comparison(sim_msg_2, sim_msg_3)

        # test messages with attributes
        attrsa = (1, 'bye')
        sim_msg_1a = ExampleSimulationMessage1(*attrsa)
        self.assertTrue(sim_msg_1a <= sim_msg_1a)
        self.assertTrue(sim_msg_1a >= sim_msg_1a)
        attrsb = (1, 'hi')
        sim_msg_1b = ExampleSimulationMessage1(*attrsb)
        self.comparison(sim_msg_1a, sim_msg_1b)

        # test messages with attributes that cannot be compared
        sim_msg_1_bad_a = ExampleSimulationMessage1(str, str)
        sim_msg_1_bad_b = ExampleSimulationMessage1(int, int)
        with self.assertRaises(TypeError):
            sim_msg_1_bad_a < sim_msg_1_bad_b


class TestSimulationMessageMeta(unittest.TestCase):

    def test_simulation_message_meta(self):
        self.assertTrue(issubclass(ExampleSimulationMessage1, SimulationMessage))
        with warnings.catch_warnings(record=True) as w:
            class BadSimulationMessage2(SimulationMessage):
                attributes = ['x']
            self.assertIn("definition does not contain a docstring", str(w[-1].message))
        warnings.simplefilter("ignore")

        self.assertEqual(ExampleSimulationMessage1.__doc__, 'My docstring')
        attr_vals = ('att1_val', 'att2_val')
        example_simulation_message = ExampleSimulationMessage1(*attr_vals)
        attrs = ['attr1', 'attr2']
        for attr,val in zip(attrs, attr_vals):
            self.assertEqual(getattr(example_simulation_message, attr), val)

        example_simulation_message2 = ExampleSimulationMessage2()
        self.assertEqual(example_simulation_message2.attrs(), [])
        self.assertEqual(example_simulation_message2.header(), None)

        with self.assertRaisesRegex(SimulatorError, 'must be a list of strings'):
            class BadSimulationMessage1(SimulationMessage):
                attributes = [2.5]

        with self.assertRaisesRegex(SimulatorError, 'contains duplicates'):
            class BadSimulationMessage2(SimulationMessage):
                attributes = ['x', 'y', 'x']
