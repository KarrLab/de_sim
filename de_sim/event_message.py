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


class EventMessageInterface(object, metaclass=ABCMeta):
    """ An abstract base class for event messages

    The comparison operations (`__gt__`, `__lt__`, etc.) order event message instances by the
    tuple (class name, instance attribute values). This enables deterministic sorting of messages
    by their content, so that event messages can be passed in a deterministic order to
    a simulation object processing them in an event.

    Attributes:
        __slots__ (:obj:`list`): use `__slots__` to save memory because a simulation may contain many messages
    """
    __slots__ = []

    def __init__(self, *args):
        """ Initialize an :obj:`EventMessage`

        Args:
            args (:obj:`tuple`): argument list for initializing a subclass instance

        Raises:
            :obj:`SimulatorError`: if `args` does not contain an argument for each entry in `__slots__`
        """
        if len(args) != len(self.__slots__):
            raise SimulatorError("Constructor for EventMessage '{}' expects {} argument(s), but "
                                 "{} provided".format(
                                     self.__class__.__name__, len(self.__slots__), len(args)))
        for slot, arg in zip(self.__slots__, args):
            setattr(self, slot, arg)

    def _values(self, to_str=False):
        """ Provide the values in an :obj:`EventMessage`

        Uninitialized attribute values are returned as `None`, or `str(None)` if `to_str` is set.

        Args:
            to_str (:obj:`bool`): if set, return `str()` of attribute values

        Returns:
            :obj:`list`: list of attribute values
        """
        vals = []
        for attr in self.__slots__:
            if hasattr(self, attr):
                if to_str:
                    vals.append(str(getattr(self, attr)))
                else:
                    vals.append(getattr(self, attr))
            else:
                if to_str:
                    vals.append(str(None))
                else:
                    vals.append(None)
        return vals

    def value_map(self):
        """ Provide a map from attribute to value, cast to strings, for this :obj:`EventMessage`

        Uninitialized values are returned as `str(None)`.

        Returns:
            :obj:`dict`: map attribute -> str(attribute value)
        """
        return {attr: val for attr, val in zip(self.__slots__, self._values(to_str=True))}

    def values(self, annotated=False, as_list=False, separator='\t'):
        """ Provide the values in this :obj:`EventMessage`

        Uninitialized values are returned as `str(None)`.

        Args:
            annotated (:obj:`bool`, optional): if set, prefix each value with its attribute name
            as_list (:obj:`bool`, optional): if set, return the attribute names in a :obj:`list`
            separator (:obj:`str`, optional): the field separator used if the attribute names
                are returned as a string

        Returns:
            :obj:`obj`: `None` if this message has no attributes, or a string representation of
                the attribute names for this :obj:`EventMessage`, or a :obj:`list`
                representation if `as_list` is set
        """
        if not self.attrs():
            return None
        if annotated:
            list_repr = ["{}:{}".format(attr, val) for attr, val in
                         zip(self.__slots__, self._values(to_str=True))]
        else:
            list_repr = self._values(to_str=True)
        if as_list:
            return list_repr
        else:
            return separator.join(list_repr)

    def __str__(self):
        """ Provide a string representation of an :obj:`EventMessage`
        """
        return "EventMessage: {}({})".format(self.__class__.__name__, self.value_map())

    def attrs(self):
        """ Provide a list of the attributes names for this :obj:`EventMessage`

        Returns:
            :obj:`list` of :obj:`str`: the attributes in this :obj:`EventMessage`
        """
        return self.__slots__

    def header(self, as_list=False, separator='\t'):
        """ Provide the attribute names for this :obj:`EventMessage`

        Args:
            as_list (:obj:`bool`, optional): if set, return the attribute names in a :obj:`list`
            separator (:obj:`str`, optional): the field separator used if the attribute names are returned
                as a string

        Returns:
            :obj:`obj`: `None` if this message has no attributes, or a string representation of
                the attribute names for this :obj:`EventMessage`, or a :obj:`list`
                representation if `as_list` is set
        """
        if not self.attrs():
            return None
        if as_list:
            return self.attrs()
        else:
            return separator.join(self.attrs())

    def __lt__(self, other):
        """ Does this :obj:`EventMessage` sort before `other`?

        Args:
            other (:obj:`EventMessage`): another :obj:`EventMessage`

        Returns:
            :obj:`bool`: `True` if this :obj:`EventMessage` sorts before `other`
        """
        return (self.__class__.__name__, self._values()) < (other.__class__.__name__, other._values())

    def __le__(self, other):
        """ Does this :obj:`EventMessage` sort before or equal `other`?

        Args:
            other (:obj:`EventMessage`): another :obj:`EventMessage`

        Returns:
            :obj:`bool`: `True` if this :obj:`EventMessage` sorts before or equals `other`
        """
        return not (other < self)

    def __gt__(self, other):
        """ Does this :obj:`EventMessage` sort after `other`?

        Args:
            other (:obj:`EventMessage`): another :obj:`EventMessage`

        Returns:
            :obj:`bool`: `True` if this :obj:`EventMessage` sorts after `other`
        """
        return (self.__class__.__name__, self._values()) > (other.__class__.__name__, other._values())

    def __ge__(self, other):
        """ Does this :obj:`EventMessage` sort after or equal `other`?

        Args:
            other (:obj:`EventMessage`): another :obj:`EventMessage`

        Returns:
            :obj:`bool`: `True` if this :obj:`EventMessage` sorts after or equals `other`
        """
        return not (self < other)


class EventMessageMeta(type):
    # attributes mapping keyword
    ATTRIBUTES = 'attributes'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __new__(cls, clsname, superclasses, namespace):
        # Short circuit when EventMessage is defined
        if clsname == 'EventMessage':
            return super().__new__(cls, clsname, superclasses, namespace)

        if '__doc__' not in namespace:
            warnings.warn("EventMessage '{}' definition does not contain a docstring.".format(
                clsname))

        attrs = {}
        if cls.ATTRIBUTES in namespace:

            # check types
            attributes = namespace[cls.ATTRIBUTES]
            if not (isinstance(attributes, list) and all([isinstance(attr, str) for attr in attributes])):
                raise SimulatorError("'{}' must be a list of strings, but is '{}'".format(
                    cls.ATTRIBUTES, attributes))

            # error if attributes contains dupes
            if not len(attributes) == len(set(attributes)):
                raise SimulatorError("'{}' contains duplicates".format(cls.ATTRIBUTES))
            attrs['__slots__'] = attributes

        new_simulation_message_class = super().__new__(cls, clsname, superclasses, attrs)
        if '__doc__' in namespace:
            new_simulation_message_class.__doc__ = namespace['__doc__'].strip()
        return new_simulation_message_class


class CombinedEventMessageMeta(ConcreteABCMeta, EventMessageMeta):
    pass


class EventMessage(EventMessageInterface, metaclass=CombinedEventMessageMeta):
    """ The event message base class

    Each simulation event contains an event message. All event messages are objects. This
    module supports compact declaration of :obj:`EventMessage` types. For example::

        class ExampleEventMessage1(EventMessage):
            ''' Docstring '''
            attributes = ['attr1', 'attr2']

    defines the `ExampleEventMessage1` class with a short docstring and two attributes.

    :obj:`EventMessage` subclasses must support the comparison operations `<`, `<=`, etc. This is
    provided automatically for attributes that support comparison. Subclasses with message attributes
    that do not support comparison must override `__lt__`, `__le__`, etc.
    """
    pass
