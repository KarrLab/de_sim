"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-01-22
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""


class Error(Exception):
    """ Base class for exceptions in `de_sim`

    Attributes:
        message (:obj:`str`): the exception's message
    """

    def __init__(self, message=None):
        super().__init__(message)


class SimulatorError(Error):
    """ Exception raised for errors in `de_sim`

    Attributes:
        message (:obj:`str`): the exception's message
    """

    def __init__(self, message=None):
        super().__init__(message)
