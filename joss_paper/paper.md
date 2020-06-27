---
title: 'DE-Sim: An Object-Oriented Discrete-Event Simulator in Python'
tags:
  - dynamical modeling
  - simulation
  - discrete-event simulation
  - object-oriented simulation
  - parallel discrete-event simulation
  - biochemical modeling
  - whole-cell modeling
  - Python
authors:
  - name: Arthur P. Goldberg
    orcid: 0000-0003-2772-1484
    affiliation: "1"
  - name: Jonathan R. Karr
    orcid: 0000-0002-2605-5080
    affiliation: "1"
affiliations:
 - name: Icahn Institute for Data Science and Genomic Technology and Department of Genetics and Genomic Sciences, Icahn School of Medicine at Mount Sinai, New York, NY 10029, USA
   index: 1
date: 20 July 2020
bibliography: paper.bib
---

# Summary

Discrete-event simulation (DES) is a simulation method that modelers use to analyze systems whose events occur at discrete instants in time.
DES models dynamically create events and determine their simulation times.
Many fields employ models that use DES, including modeling of biochemical dynamics, computer network performance analysis, war gaming, modeling of infectious disease transmission, and others [@banks2005discrete].

The construction of a DES model can be simplified and accelerated by using a DES simulator that implements the generic features needed by all DES models, primarily efficient execution of events in increasing simulation time order.
Model construction can be further enhanced, and models can be made more comprehensible and reusable, by structuring models as object-oriented programs.
This approach, known as *object-oriented discrete-event simulation* (OO DES), recommends that models represent entities in the system being modeled as objects, and represent interactions between entities as event messages exchanged between objects.
OO DES was invented in the 1960s by the SIMULA language [@dahl1966simula; @nygaard1978development] and continues to be used by modern tools such as SystemC [@mueller2001simulation; @ieee2012ieee] and SIMUL8 [@concannon2003dynamic].

DE-Sim is a Python package that supports OO DES simulations.

# Research purpose

DE-Sim is needed by researchers who want to build OO DES models in Python because existing open source Python simulators do not support an object-oriented, message-passing interface.
We have used DE-Sim as a platform for a simulator of whole-cell models that comprehensively represent the biochemical dynamics in individual biological cells [@goldberg2020wc_sim; @goldberg2018emerging].
The whole-cell simulator (WC-Sim) models the growth of a cell and the changes in its biochemical composition caused by chemical reactions and the intracellular movement of molecules.
To comprehensively represent the numerous processes in a cell, such as metabolism, transcription, and translation, WC-Sim must use multiple types of dynamic integration algorithms, including ordinary differential equations and the stochastic simulation algorithm.
DE-Sim's OO DES framework enabled the construction of WC-Sim.
WC-Sim uses different DE-Sim object types to represent different integration algorithms, and uses
DE-Sim's discrete-event scheduling to synchronize the interactions between these integration algorithms.

Another benefit of implementing models in the object-oriented, message-passing framework supported by DE-Sim is that parallel DES simulation can reduce the runtimes of their simulations, which are often inconveniently long.
The OO DES framework makes parallel simulation feasible because 1) objects that do not share memory references can be distributed on multiple processors, and 2) a parallel DES simulator interfaces with simulation objects through the event messages that they use to schedule events [@Jefferson1985; @Barnes2013; @Carothers2000].
An example research model accelerated by parallel simulation analyzes epidemic outbreak phenomena [@perumalla2012discrete].
We plan to speed up whole-cell models of human cells with parallel simulation in future work [@goldberg2016toward].

# DE-Sim features

A OO DES application that uses DE-Sim can be defined in three steps:

1: Create event message types by subclassing `SimulationMessage`.

```python
class MessageSentToSelf(SimulationMessage):
    "A message type with no attributes"

class MessageWithAttribute(SimulationMessage):
    'An event message type with an attribute'
    attributes = ['attr_1']
```

An event message class must be documented by a docstring, and may include attributes.

2: Define simulation application objects by subclassing `ApplicationSimulationObject`.

```python
class SimpleSimulationObject(ApplicationSimulationObject):

    def __init__(self, name, delay):
        self.delay = delay
        super().__init__(name)

    def send_initial_events(self):
        self.send_event(self.delay, self, MessageSentToSelf())

    def handle_simulation_event(self, event):
        self.send_event(self.delay, self, MessageSentToSelf())

    event_handlers = [(MessageSentToSelf, handle_simulation_event)]

    # register the message types sent
    messages_sent = [MessageSentToSelf]
```

Each simulation object must have a unique `name`.
This example adds an instance attribute that provides the delay between events.
All `ApplicationSimulationObject`s also have a read-only attribute called `time` that always provides the current simulation time.

A simulation object may include a `send_initial_events` method, which, if present, will be called by the simulator during initialization to send the object's initial events.
A simulation must send at least one initial event.

A simulation object must include at least one method that handles simulation events.
The simulator vectors incoming message types as directed by an `event_handlers` attribute that associates each message type received by a simulation object with one of its methods.

`ApplicationSimulationObject` provides the method
`send_event(delay, receiving_object, event_message)` which schedules an event to occur `delay` time units in the future.
`event_message` is an instance of a `SimulationMessage`, and may have attributes that contain data used by the event.
The event will be executed by an event handler in simulation object `receiving_object`, which will receive a simulation event containing `event_message` at its scheduled simulation time.
In this example all simulation events are scheduled to be executed by the object that creates the event, but realistic
simulations contain multiple simulation objects which schedule events for each other.

3: Execute a simulation by creating a `SimulationEngine`, instantiating the application objects, sending their initial event messages, and running the simulation.

```python
# create a simulation engine
simulation_engine = SimulationEngine()

# create a simulation object and add it to the simulation
simulation_engine.add_object(SimpleSimulationObject('object_1', 6))

# initialize and run the simulation
simulation_engine.initialize()
num_events = simulation_engine.run(25)
```
This runs a simulation for 25 time units, and obtains the number of events executed.

DE-Sim offers many additional features:

* Simple configuration from files
* Optional periodic checkpoints
* Quick construction of periodic simulation objects from a template
* Control of simulation termination by a user-defined Python function that returns a boolean
* Recording of simulation run metadata, including start time, run time, and IP address
* Visualization of simulation run event messages trace
* Extensive error detection
* Logging
* Performance profiling that uses Python's `cProfile` package
* Memory use analysis that uses Python's `pympler.tracker` package
* Extensive documentation
* Unit tests with 98% coverage

# Visualization of simulation traces

DE-Sim generates space-time visualizations of event traces that help debug and understand an OO DES application.
\autoref{fig:phold_space_time_plot} visualizes a simulation run of the PHOLD parallel DES benchmark [@fujimoto1990performance; @Barnes2013] (see `phold.py` in DE-Sim's `examples` directory).
This simulation parameterizes PHOLD as follows.
An event schedules another event to occur after an exponentially distributed delay with $\mu=1$.
An object schedules the next event for itself with probability 0.5; otherwise the next event is scheduled for another PHOLD object selected at random.

![A space-time visualization of all messages and events in an 8 time unit simulation of PHOLD.
A timeline for each object shows its events as gray dots.
Event messages are shown as arrows, with the arrow tail located at the (object instance, simulation time) coordinates when an event message was created and sent, and the arrow head located at the coordinates when the event message is executed.
At time 0 each PHOLD object sends an initialization message to itself.
Curved blue arrows represent event messages sent by objects to themselves, while straight purple arrows illustrate messages sent to another object.
\label{fig:phold_space_time_plot}](phold_space_time_plot.png)

# DE-Sim performance

DE-Sim achieves good performance by using Python's `heapq` priority queue package to schedule events.
\autoref{fig:performance} reports the performance of DE-Sim over a range of simulation sizes.

![Performance of DE-Sim executing a simulation that sends events around a cycle of objects.
We present the statistics of three runs made in a Docker container executing on a 2.9 GHz Intel Core i5 processor in a MacBook.
\label{fig:performance}](performance.png)

# Availability

DE-Sim is freely and openly available under the MIT license at the locations below.

* Python package: [https://pypi.org/project/de-sim/](https://pypi.org/project/de-sim/)
* Docker image: [https://hub.docker.com/r/karrlab/de_sim](https://hub.docker.com/r/karrlab/de_sim)
* Documentation, including installation instructions, examples, and API documentation: [https://docs.karrlab.org/de_sim/](https://docs.karrlab.org/de_sim/)
* Issue tracker: [https://github.com/KarrLab/de_sim/issues/](https://github.com/KarrLab/de_sim/issues/)
* Source code and guide for contributing to DE-Sim: [https://github.com/KarrLab/de_sim/](https://github.com/KarrLab/de_sim/)
* Continuous integration: [http://circleci.com/gh/KarrLab/de_sim/](http://circleci.com/gh/KarrLab/de_sim/)

DE-Sim requires [Python](https://www.python.org/) 3.6 or higher and [pip](https://pip.pypa.io/).

This article discusses version 0.0.2 of DE-Sim.

# Acknowledgements

This worked was supported by National Science Foundation award 1649014 and National
Institutes of Health award R35GM119771 to J.R.K.

# References
