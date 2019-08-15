""" Simulation core utilities

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-26
:Copyright: 2018, Karr Lab
:License: MIT
"""
from abc import ABCMeta, abstractmethod


class ConcreteABCMeta(ABCMeta):
    """ A concrete subclass of ABCMeta that's used to combine meta classes

    In particular, this makes it easy to create a "most derived metaclass" that includes
    ABCMetas and a custom Meta, and avoid "TypeError: metaclass conflict".

    See https://docs.python.org/3/reference/datamodel.html#determining-the-appropriate-metaclass,
    PEP 3119 and https://stackoverflow.com/a/31429212
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.__abstractmethods__:
            raise TypeError("{} has not implemented abstract methods {}".format(
                self.__name__, ", ".join(self.__abstractmethods__)))
