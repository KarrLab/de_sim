""" Simulation utilities

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-26
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""
from abc import ABCMeta
from logging2 import LogLevel
from progressbar import widgets
from progressbar.bar import ProgressBar


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

    Shows the progress of a simulation towards the time it is scheduled to end, in simulation time.

    A `SimulationProgressBar` does nothing by default, so that it can be used without an
    `if` statement and configured at runtime.
    """

    def __init__(self, use=False):
        """ Create a simulation progress bar

        Args:
            use (:obj:`bool`): whether to use a progress bar
        """
        self.use = use

    def start(self, max_time):
        """ Start the simulation's progress bar

        Args:
            max_time (:obj:`float`): the simulation's end time
        """
        if self.use:
            self.bar = ProgressBar(
                widgets=[
                    widgets.Percentage(),
                    ' ', widgets.SimpleProgress(
                        format='%(value)d/%(max_value)d (max_time)'),
                    ' ', widgets.Bar(),
                    ' ', widgets.Timer(),
                    ' ', widgets.AdaptiveETA(),
                ],
                max_value=max_time).start()

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


class FastLogger(object):
    """ Cache activity decision to avoid slow logging when not writing logs

    Attributes:
        active (:obj:`bool`): whether the log is active
        method (:obj:`method`): the logging method being used, `debug`, `info`, etc.
    """
    LOG_LEVELS = set([log_level.name for log_level in LogLevel])

    def __init__(self, logger, level_used):
        """
        Args:
            logger (:obj:`logging2.Logger`): a logger
            level_used (:obj:`str`): a logging level, as used in :obj:`logging2.LogLevel`:
        """
        self.active = FastLogger.active_logger(logger, level_used)
        self.method = getattr(logger, level_used)
        self.logger = logger

    @staticmethod
    def active_logger(logger, level_used):
        """ Determine whether the logger will write log messages

        Args:
            logger (:obj:`logging2.Logger`): a logger
            level_used (:obj:`str`): the logging level for this logger

        Returns:
            :obj:`bool`: return `True` if the `logger` is active, `False` otherwise

        Raises:
            :obj:`ValueError`: if `level_used` is not a valid logging level
        """
        if level_used not in FastLogger.LOG_LEVELS:
            raise ValueError("bad level '{}'".format(level_used))
        log_level = LogLevel[level_used]
        active = False
        for handler in logger.handlers:
            if handler.min_level <= log_level:
                active = True
        return active

    def is_active(self):
        """ Get the cached active state of this logger

        Returns:
            :obj:`bool`: whether this logger is active
        """
        return self.active

    def get_level(self):
        """ Get the level of this logger

        Returns:
            :obj:`LogLevel`: the level of this logger
        """
        min_of_min = LogLevel.exception
        for handler in self.logger.handlers:
            if handler.min_level < min_of_min:
                min_of_min = handler.min_level
        return min_of_min

    def fast_log(self, msg, **kwargs):
        """ Log, and do it quickly if nothing is being written

        Args:
            msg (:obj:`str`): the log message
            kwargs (:obj:`dict`): other logging arguments
        """
        if self.active:
            self.method(msg, **kwargs)
