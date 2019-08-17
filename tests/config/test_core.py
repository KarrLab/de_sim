""" Config tests

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2019-08-15
:Copyright: 2019, Karr Lab
:License: MIT
"""

import unittest
import logging2

from de_sim.config import core
from wc_utils.debug_logs.core import DebugLogsManager

class TestCore(unittest.TestCase):

    def test_get_config(self):
        config = core.get_config()
        self.assertEqual(config['de_sim']['copy_event_bodies'], False)
        config = core.get_config(extra={'de_sim': {
                                        'copy_event_bodies': True
                                                  }
                                       })
        self.assertEqual(config['de_sim']['copy_event_bodies'], True)

    def test_get_debug_logs(self):
        # test conf hierarchy from debug.default.cfg
        c = core.get_debug_logs_config()
        for key in ['debug_logs', 'handlers', 'debug.console', 'level']:
            self.assertTrue(key in c)
            c = c[key]

        debug_log_manager = core.get_debug_logs()
        self.assertTrue(isinstance(debug_log_manager, DebugLogsManager))
        self.assertTrue(isinstance(debug_log_manager.get_log('wc.debug.file'), logging2.loggers.Logger))
