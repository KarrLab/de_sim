""" Simulation utilities

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-26
:Copyright: 2018, Karr Lab
:License: MIT
"""
from abc import ABCMeta, abstractmethod
from progressbar.bar import ProgressBar
from progressbar import widgets


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


class SimulationProgressBar(object):
    """ Simulation progress bar

    Shows the progress of a simulation towards the time it is scheduled to end, in simulation time
    """

    def __init__(self, use=False):
        """ Create a simulation progress bar

        A `SimulationProgressBar` does nothing by default, so that it can be used without an
        `if` statement and configured at run-time.

        Args:
            use (:obj:`bool`): whether to use a progress bar
        """
        self.use = use

    def start(self, end_time):
        """ Start the simulation's progress bar

        Args:
            end_time (:obj:`float`): the simulation's end time
        """
        if self.use:
            self.bar = ProgressBar(
                widgets=[
                    widgets.Percentage(),
                    ' ', widgets.SimpleProgress(
                        format='%(value)d/%(max_value)d (end_time)'),
                    ' ', widgets.Bar(),
                    ' ', widgets.Timer(),
                    ' ', widgets.AdaptiveETA(),
                ],
                max_value=end_time).start()

    def progress(self, sim_time):
        """ Advance the simulation's progress bar

        Args:
            sim_time (:obj:`float`): the simulation time
        """
        if self.use:
            self.bar.update(sim_time)

    def end(self):
        """ End the simulation's progress bar
        """
        if self.use:
            self.bar.finish()
