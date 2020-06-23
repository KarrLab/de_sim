"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-06-23
:Copyright: 2020, Karr Lab
:License: MIT
"""

import numpy
import unittest

from de_sim.visualize import EventCoordinates, EventMessage, SpaceTime


class TestVisualize(unittest.TestCase):

    def setUp(self):
        self.sample_data = [
            EventMessage('self_msg',
                         EventCoordinates('obj_1', 0),
                         EventCoordinates('obj_1', 2)),
            EventMessage('self_msg',
                         EventCoordinates('obj_2', 0),
                         EventCoordinates('obj_2', 1)),
            EventMessage('other_msg',
                         EventCoordinates('obj_2', 1),
                         EventCoordinates('obj_1', 3)),
            EventMessage('other_msg',
                         EventCoordinates('obj_1', 0),
                         EventCoordinates('obj_3', 2.5)),
        ]

    def test(self):
        space_time = SpaceTime(self.sample_data)
        self.assertEqual(space_time.get_object_ids(), 'obj_1 obj_2 obj_3'.split())
        self.assertEqual(space_time.get_min_max_times(), (0, 3))
        numpy.testing.assert_array_almost_equal(space_time.get_obj_x_locations(), [1/6, 3/6, 5/6])
        self.assertTrue(isinstance(space_time.get_obj_x_locations_map(), dict))
        numpy.testing.assert_array_almost_equal(space_time.get_event_locations(),
                                                [(1/6, 0),
                                                 (1/6, 2),
                                                 (1/2, 0),
                                                 (1/2, 1),
                                                 (1/2, 1),
                                                 (1/6, 3),
                                                 (1/6, 0),
                                                 (5/6, 2.5)])
        self.assertEqual(space_time.get_categorized_messages(),
            (self.sample_data[0:2],
             self.sample_data[2:]))
        space_time.plot_data('filename.png')
