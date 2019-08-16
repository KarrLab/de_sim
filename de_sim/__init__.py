import pkg_resources

# read version
with open(pkg_resources.resource_filename('de_sim', 'VERSION'), 'r') as file:
    __version__ = file.read().strip()

from . import config
from . import errors
from . import event
from . import shared_state_interface
from . import simulation_engine
from . import simulation_message
from . import simulation_object
from . import utilities
