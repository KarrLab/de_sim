""" Base class for event messages

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2017-03-26
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

from abc import ABCMeta
import warnings

from de_sim.errors import SimulatorError
from de_sim.utilities import ConcreteABCMeta


class EventMessageNormalTop3(object):
    """ A 'normal' event message base class

    """
    def __init__(self):
        pass



class EventMessageNormalBottom3(object):
    """ A 'normal' event message base class

    """
    def __init__(self):
        pass


