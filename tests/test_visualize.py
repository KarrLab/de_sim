"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-06-23
:Copyright: 2020, Karr Lab
:License: MIT
"""

import numpy
import os
import shutil
import tempfile
import unittest

from de_sim.visualize import EventCoordinates, SimulationEventMessage, SpaceTime


class TestVisualize(unittest.TestCase):

    def setUp(self):
        self.sample_data = [
            SimulationEventMessage('self_msg',
                         EventCoordinates('obj_1', 0),
                         EventCoordinates('obj_1', 2)),
            SimulationEventMessage('self_msg',
                         EventCoordinates('obj_2', 0),
                         EventCoordinates('obj_2', 1)),
            SimulationEventMessage('other_msg',
                         EventCoordinates('obj_2', 1),
                         EventCoordinates('obj_1', 3)),
            SimulationEventMessage('other_msg',
                         EventCoordinates('obj_1', 0),
                         EventCoordinates('obj_3', 2.5)),
        ]
        self.out_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.out_dir)

    def test(self):
        space_time = SpaceTime(self.sample_data)
        self.assertEqual(space_time.get_object_ids(), 'obj_1 obj_2 obj_3'.split())
        self.assertEqual(space_time.get_min_max_times(), (0, 3))
        numpy.testing.assert_array_almost_equal(space_time.get_obj_x_locations(), [1 / 6, 3 / 6, 5 / 6])
        self.assertTrue(isinstance(space_time.get_obj_x_locations_map(), dict))
        numpy.testing.assert_array_almost_equal(space_time.get_event_locations(),
                                                [(1 / 6, 0),
                                                 (1 / 6, 2),
                                                 (1 / 2, 0),
                                                 (1 / 2, 1),
                                                 (1 / 2, 1),
                                                 (1 / 6, 3),
                                                 (1 / 6, 0),
                                                 (5 / 6, 2.5)])
        self.assertEqual(space_time.get_categorized_messages(),
                         (self.sample_data[0:2],
                          self.sample_data[2:]))
        plot_file = os.path.join(self.out_dir, 'filename.png')
        space_time.plot_data(plot_file)
        self.assertTrue(os.path.isfile(plot_file))

    def test_get_data(self):
        PLOT_LOG = os.path.join(os.path.dirname(__file__), 'fixtures', 'example.de_sim.plot.log')
        space_time = SpaceTime()
        ems = space_time.get_data(PLOT_LOG)
        self.assertEqual(len(ems), 5)
        self.assertEqual(ems[0],
                         SimulationEventMessage(message_type='InitMsg',
                                      send_coordinates=EventCoordinates(sim_obj_id='obj_2', time=0.0),
                                      receive_coordinates=EventCoordinates(sim_obj_id='obj_2', time=0.044)))
        self.assertEqual(ems[4],
                         SimulationEventMessage(message_type='MessageSentToOtherObject',
                                      send_coordinates=EventCoordinates(sim_obj_id='obj_1', time=0.863),
                                      receive_coordinates=EventCoordinates(sim_obj_id='obj_2', time=1.731)))
