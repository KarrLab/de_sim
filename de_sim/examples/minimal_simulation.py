""" A minimal simulation, containing one simulation object.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-27
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""
import argparse

import de_sim


class MessageSentToSelf(de_sim.EventMessage):
    "A message that's sent to self"


class MinimalSimulationObject(de_sim.SimulationObject):
    """ :obj:`~de_sim.simulation_object.SimulationObject` subclasses represent the state of a simulation and the
        actions that schedule and handle events
    """

    def __init__(self, name, delay):
        self.delay = delay
        super().__init__(name)

    def init_before_run(self):
        """ Initialize before a simulation run; called by the simulator """
        self.send_event(self.delay, self, MessageSentToSelf())

    def handle_simulation_event(self, event):
        """ Handle a simulation event """
        del event   # Avoid warning W0613, unused-argument
        # Schedule an event `self.delay` in the future
        # The event will be received by this simulation object, and contain a `MessageSentToSelf` instance
        self.send_event(self.delay, self, MessageSentToSelf())

    # declare that events that contain a `MessageSentToSelf` message should be handled by `handle_simulation_event`
    event_handlers = [(MessageSentToSelf, handle_simulation_event)]

    # register the message types sent by this simulation object
    messages_sent = [MessageSentToSelf]


class RunMinimalSimulation(object):

    @staticmethod
    def parse_args(cli_args=None):
        """ Parse command line arguments

        Args:
            cli_args (:obj:`list`, optional): if provided, use to test command line parsing

        Returns:
            :obj:`argparse.Namespace`: parsed command line arguments
        """
        parser = argparse.ArgumentParser(description="A minimal simulation, containing one simulation object")
        parser.add_argument('delay', type=float, help="Delay between events")
        parser.add_argument('max_time', type=float, help="End time for the simulation")
        if cli_args is not None:
            args = parser.parse_args(cli_args)
        else:    # pragma: no cover     # reachable only from command line
            args = parser.parse_args()
        return args

    @staticmethod
    def main(args):

        # create a simulator
        simulator = de_sim.Simulator()

        # create a simulation object and add it to the simulation
        simulator.add_object(MinimalSimulationObject('minimal_sim_obj', args.delay))

        # run the simulation
        simulator.initialize()
        return simulator.simulate(args.max_time).num_events


if __name__ == '__main__':  # pragma: no cover     # reachable only from command line
    try:
        args = RunMinimalSimulation.parse_args()
        num_events = RunMinimalSimulation.main(args)
        print(f"Executed {num_events} events")
    except KeyboardInterrupt:
        pass
