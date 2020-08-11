""" A simulation of a random walk where a variable is incremented or decremented with equal probability at each event

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-27
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""
import argparse
import matplotlib.pyplot as plt
import random

import de_sim


class RandomStepMessage(de_sim.EventMessage):
    "An event message class that specifies a random step"
    attributes = ['step']


class RandomWalkSimulationObject(de_sim.SimulationObject):
    """ A one-dimensional random walk model, with random times between steps

    Each step moves either -1 or +1, with equal probability.
    The delay between steps is 1 or 2, also with equal probability.

    Attributes:
        name (:obj:`str`): this simulation object's name, which is unique across all simulation objects
        state (:obj:`int`): the current position; initialized to 0
        history (:obj:`dict` of :obj:`list`): the walk's position as a function of time
    """

    def __init__(self, name):
        super().__init__(name)

    def schedule_next_step(self):
        """ Schedule the next event, a step that moves -1 or +1 with equal probability """
        step = random.choice([-1, +1])
        # the time between steps is randomly 1 or 2, with equal probability
        self.send_event(random.choice([1, 2]), self, RandomStepMessage(step))

    def init_before_run(self):
        """ Initialize before a simulation run; called by the simulator

        Schedule the first event
        """
        self.position = 0
        self.history = {'times': [0],
                        'positions': [0]}
        self.schedule_next_step()

    def handle_step_event(self, event):
        """ Handle a step event

        Update the position and history
        """
        step = event.message.step
        self.position += step
        self.history['times'].append(self.time)
        self.history['positions'].append(self.position)
        self.schedule_next_step()

    # event_handlers is a list of pairs that maps each event message type
    # received by this simulation object class to the method that handles
    # the event message class
    event_handlers = [(RandomStepMessage, handle_step_event)]

    # messages_sent registers all message types sent by this object
    messages_sent = [RandomStepMessage]


class RunRandomWalkSimulation(object):

    @staticmethod
    def parse_args(cli_args=None):  # pragma: no cover  # don't bother testing
        """ Parse command line arguments

        Args:
            cli_args (:obj:`list`, optional): if provided, use to test command line parsing

        Returns:
            :obj:`argparse.Namespace`: parsed command line arguements
        """
        parser = argparse.ArgumentParser(
            description="A random walk on the integer number line with random times between steps")
        parser.add_argument('max_time', type=float, help="End time for the simulation")
        parser.add_argument('--no-output', dest='output', action='store_false', help="Don't write walk history to stdout")
        if cli_args is not None:
            args = parser.parse_args(cli_args)
        else:    # pragma: no cover     # reachable only from command line
            args = parser.parse_args()
        return args

    @staticmethod
    def main(args):

        # create a simulator
        simulator = de_sim.Simulator()

        # create a RandomWalkSimulationObject and add it to the simulation
        random_walk_sim_obj = RandomWalkSimulationObject('random walk simulation object')
        simulator.add_object(random_walk_sim_obj)

        # run the simulation
        simulator.initialize()
        num_events = simulator.simulate(args.max_time).num_events

        # print the random walk
        if args.output:
            print(f'Random walk:')
            for time, pos in zip(random_walk_sim_obj.history['times'],
                                 random_walk_sim_obj.history['positions']):
                print(f"{time:4.0f}{pos:>6}")

        # plot the random walk as a step function
        plt.step(random_walk_sim_obj.history['times'], random_walk_sim_obj.history['positions'])
        plt.xlabel('time')
        plt.ylabel('position')
        plt.show()

        return num_events


if __name__ == '__main__':  # pragma: no cover     # reachable only from command line
    try:
        args = RunRandomWalkSimulation.parse_args()
        RunRandomWalkSimulation.main(args)
    except KeyboardInterrupt:
        pass
