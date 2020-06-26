# example message types:
from de_sim.simulation_message import SimulationMessage


class InitMsg(SimulationMessage):
    'An InitMsg message'


class Eg1(SimulationMessage):
    'Eg1 simulation message'


class MsgWithAttrs(SimulationMessage):
    'MsgWithAttrs simulation message'
    attributes = ['attr1', 'attr2']


class UnregisteredMsg(SimulationMessage):
    'Unregistered simulation message'
