""" Setup simulator core configuration

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-10-05
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""

from .config import core as config_core
from wc_utils.debug_logs.core import DebugLogsManager

# setup debug logs
config = config_core.get_debug_logs_config()
logs = DebugLogsManager().setup_logs(config)
