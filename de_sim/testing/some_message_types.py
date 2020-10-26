# example message types:
from de_sim.event_message import EventMessage


class InitMsg(EventMessage):
    'An InitMsg message'


class Eg1(EventMessage):
    'Eg1 event message'


class MsgWithAttrs(EventMessage):
    'MsgWithAttrs event message'
    attr1: int
    attr2: str


class UnregisteredMsg(EventMessage):
    'Unregistered event message'
