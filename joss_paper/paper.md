---
title: 'DE-Sim: an object-oriented, discrete-event simulation tool for data-intensive modeling of complex systems in Python'
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
date: 18 August 2020
bibliography: paper.bib
---

# Summary

Recent advances in data collection, storage, and sharing have created unprecedented opportunities to gain insights into complex systems such as the biochemical networks that generate cellular behavior. 
Understanding the behavior of such systems will likely require larger and more comprehensive dynamical models that are based on a combination of first principles and empirical data.
These models will likely represent each component and interaction using mechanistic approximations that are derived from first principles and calibrated with data. For example, dynamical models of biochemical networks often represent the interactions among molecules as chemical reactions whose rates are determined by combining approximations of chemical kinetics and empirically-observed reaction rates.
Furthermore, complex models that represent multiple types of components and their interactions will require diverse approximations and large, heterogeneous datasets. New tools are needed to build and simulate such complex, data-intensive models.

One of the most promising methods for building and simulating complex, data-intensive models is discrete-event simulation (DES). DES represents the dynamics of a system as a sequence of instantaneous events [@fishman2013discrete]. DES is used by a wide range of research, such as studying the dynamics of biochemical networks, characterizing the performance of computer networks, evaluating potential war strategies, and forecasting epidemics [@banks2005discrete].
Although multiple DES tools exist, it remains difficult to build and simulate complex, data-intensive models.  First, it is cumbersome to create complex models with the low-level languages supported by many of the existing tools. Second, most of the existing tools are siloed from the ecosystems of data science tools that are exploding around Python and R.

To address this problem, we developed DE-Sim ([https://github.com/KarrLab/de_sim](https://github.com/KarrLab/de_sim)), an open-source, object-oriented (OO), Python-based DES tool.
DE-Sim helps researchers model complex systems by enabling them to use Python's powerful OO features to manage multiple types of components and multiple types of interactions.
By building upon Python, DE-Sim also makes it easy for researchers to use Python's powerful data science tools, such as pandas [@mckinney2010data] and SciPy [@virtanen2020scipy], to incorporate large, heterogeneous datasets into comprehensive and detailed models.
We anticipate that DE-Sim will enable a new generation of models that capture systems with unprecedented breadth and depth.
For example, we are using DE-Sim to develop a multi-algorithmic simulation tool for whole-cell models [@karr2015principles; @goldberg2018emerging; @karr2012whole] that predict phenotype from genotype by capturing all of the biochemical activity in a cell.

Here, we describe the need for new tools for building and simulating more comprehensive and more detailed models, outline how DE-Sim addresses this need, and present a brief tutorial that describes how to build and simulate models with DE-Sim. In addition, we summarize the strengths of DE-Sim over existing DES tools, we report the simulation performance of DE-Sim, and we present a case study of how we are using DE-Sim to develop a tool for simulating whole-cell models. Finally, we outline our plans to increase the performance of models built with DE-Sim. Additional examples, tutorials, and documentation are available online, as described in the 'Availability of DE-Sim' section below.

# Need for tools for building and simulating complex, data-intensive models

Many scientific fields can now collect detailed data about the components of complex systems and their interactions. For example, deep sequencing has dramatically increased the availability of molecular data about biochemical networks. Combined with advances in computing, we believe that it is now possible to use this data and first principles to create comprehensive and detailed models that can provide new insights into complex systems. For example, deep sequencing and other molecular data can be used to build whole-cell models.

Achieving such comprehensive and detailed models will likely require integrating disparate principles and diverse data. While there are several DES tools, such as SimEvents [@clune2006discrete] and SimPy [@matloff2008introduction], and numerous tools for working with large, heterogeneous datasets, such as pandas and SQLAlchemy [@bayer2020sqlalchemy], it is difficult to use these tools in combination. As a result, despite having all of the major ingredients, it remains difficult to build and simulate complex, data-intensive models.

# DE-Sim provides critical features for building and simulating complex, data-intensive models

DE-Sim simplifies the construction and simulation of *discrete-event models* through several features. First, DE-Sim structures discrete-event models as OO programs [@zeigler1987hierarchical]. This structure enables researchers to use classes of *simulation objects* to encapsulate the complex logic required to represent each *model component*, and use classes of *event messages* to encapsulate the logic required to describe their *interactions*. With DE-Sim, users define classes of simulation objects by creating subclasses of DE-Sim's simulation object class. DE-Sim simulation object classes can exploit all the features of Python classes. For example, users can encode relationships between the types of components in a model into hierarchies of subclasses of simulation objects. As a concrete example, a model of the biochemistry of RNA transcription and protein translation could be implemented using a superclass that captures the behavior of polymers and three subclasses that represent the specific properties of DNAs, RNAs, and proteins. DE-Sim makes it easy to model complex systems that contain multiple types of components through multiple classes of simulation objects. Users can model arbitrarily many instances of each type of component by creating multiple instances of the corresponding simulation object class. 

Second, by building on top of Python, DE-Sim makes it easy for researchers to use Python's extensive suite of data science tools to build complex models from heterogeneous, multidimensional datasets. For example, researchers can use tools such as H5py, ObjTables [@karr2020objtables], pandas, requests, and SQLAlchemy to retrieve diverse data from spreadsheets, HDF5 files, REST APIs, databases, and other sources; use tools such as NumPy [@oliphant2006guide] to integrate this data into a unified model; and use tools such as LMFIT, Pyomo [@hart2011pyomo], and SciPy to calibrate models. DE-Sim also makes it easy to use many of these same tools to analyze simulation results.

DE-Sim also provides several features to help users execute, analyze, and debug simulations:

* **Stop conditions:** DE-Sim makes it easy to terminate simulations when specific criteria are reached. Researchers can specify stop conditions as functions that return true when the simulation should conclude.
* **Results checkpointing:** DE-Sim makes it easy to record the results of simulations through an easily-configurable checkpointing module.
* **Space-time visualizations:** DE-Sim can generate space-time visualizations of simulation trajectories (\autoref{fig:phold_space_time_plot}). These diagrams can help researchers understand and debug simulations.
* **Reproducible simulations:** To help researchers debug simulations, repeated executions of the same simulation with the same configuration and same random number generator seed produce the same results.

![**DE-Sim can generate space-time visualizations of simulation trajectories.** 
This figure illustrates a space-time visualization of all of the events and messages in a simulation of the parallel hold (PHOLD) DES benchmark model [@fujimoto1990performance] with three simulation objects. The timeline (grey line) for each object shows its events (grey dots). The blue and purple arrows illustrate events scheduled by simulation objects for themselves and other objects, respectively. The code for this simulation is available in the DE-Sim Git repository. 
\label{fig:phold_space_time_plot}](phold_space_time_plot.pdf)

Together, we believe that these features can simplify and accelerate the development of complex, data-intensive models.

# Comparison of DE-Sim with existing discrete-event simulation tools

Although there are several other DES tools, we believe that DE-Sim uniquely facilitates data-intensive modeling through a novel combination of OO modeling and support for numerous high-level data science tools. \autoref{fig:comparison} compares the features and characteristics of DE-Sim and some of the most popular DES tools.

![**Comparison of DE-Sim with some of the most popular DES tools.**
DE-Sim is the only open-source, OO DES tool based on Python.
This combination of features makes DE-Sim uniquely suitable for creating and simulating complex, data-intensive models. 
\label{fig:comparison}](comparison.pdf)

SimPy is an open-source DES tool that enables users to use functions to create simulation processes. As another Python-based tool, SymPy also makes it easy for researchers to leverage the Python ecosystem to build models. However, we believe that DE-Sim makes it easier for researchers to build complex models by enabling them to implement models as collections of classes rather than collections of functions. In addition, we believe that DE-Sim is simpler to use because DE-Sim supports a uniform approach for scheduling events, whereas SimPy simulation processes must use two different approaches to schedule events for themselves and each other.

SimEvents is a library for DES within the MATLAB/Simulink environment. While SimEvents' graphical interface makes it easy to create simple models, we believe that DE-Sim makes it easier to implement more complex models. By building upon Python, a rich OO language, DE-Sim makes it easier for modelers to leverage OO programming to manage complex simulations than SimEvents, which builds upon MATLAB, a primarily functional language. By making it easy to use a variety of Python-based data science tools, DE-Sim also makes it easier to use data to create models than SimEvents, which builds on a more limited ecosystem of data science tools.

SystemC is a `C++`-based OO DES tool that is frequently used to model digital systems [@mueller2001simulation]. While SystemC provides many of the same core features as DE-Sim, we believe that DE-Sim is more accessible to researchers than SystemC because DE-Sim builds upon Python, which is more popular than `C++` in many fields of research.

SIMSCRIPT III [@rice2005simscript] and SIMUL8 [@concannon2003dynamic] are commercial DES tools that enable researchers to implement models using proprietary languages. SIMSCRIPT III is well-suited to modeling decision support systems for domains such as war-gaming, communications networks, transportation, and manufacturing, and SIMUL8 is well-suited to modeling business processes. However, we believe that DE-Sim is more powerful for most scientific and engineering fields because DE-Sim can leverage Python's robust ecosystem of data science packages.

# Tutorial: Building and simulating models with DE-Sim

Users can define and execute a DE-Sim model of a system in three steps: (1) implement event message classes that represent the interactions between the components of the system, (2) implement simulation object classes that represent the states of the components of the system and their actions that initiate and respond to interactions, and (3) use instances of these classes to build and simulate the model.
Here, we illustrate these steps with a model of a random walk on the integer number line. The random walk steps forward or backward with equal probability. The walk takes steps every one or two time units with equal likelihood. This tutorial and additional tutorials are also available as interactive Jupyter notebooks at [https://sandbox.karrlab.org/tree/de_sim](https://sandbox.karrlab.org/tree/de_sim)).

1: Create an event message class to represent steps.

Create a subclass of `de_sim.EventMessage` to represent steps. Use the instance attribute `step_value` to capture the magnitude and direction of a step. Declare that the `step_value` instance attribute represents the data carried by the message by setting the class attribute `msg_field_names` to a list with the single element `step_value`. The `msg_field_names` attribute is similar to the `field_names` parameter used by Python’s `namedtuple` factory function. Arguments to an `EventMessage`’s constructor are assigned in order to the attributes listed in `msg_field_names`. The simulation objects which execute steps will use this `step_value` attribute to change the position of the random walk.

```python
import de_sim

class RandomStepMessage(de_sim.EventMessage):
    " An event message storing the value of a step of a random walk "
    msg_field_names = ['step_value']

```

2: Define a simulation object class that represents the position of the random walk and schedules and executes random steps.

Simulation objects are like threads, in that a simulation's scheduler decides when to execute them, and their execution is suspended when they have no work to do.
But DES simulation objects and threads are scheduled by different algorithms.
Whereas a traditional scheduler executes threads whenever they have work to do,
a DES scheduler executes simulation objects to ensure that events occur in simulation time order, as summarized by the fundamental invariant of discrete-event simulation: all events in a simulation are executed in non-decreasing time order.

By guaranteeing this behavior, the DE-Sim scheduler ensures that causality relationships between events are respected.
(The invariant says *non-decreasing* time order, and not *increasing* time order, because events can occur simultaneously, as discussed in DE-Sim’s Jupyter notebooks.)

This invariant has two consequences:

* All synchronization between simulation objects is controlled by the simulation times of events.
* Each simulation object executes its events in non-decreasing time order. 

The Python classes that generate and handle simulation events are simulation object classes, which are defined as subclasses of `de_sim.SimulationObject`.
DE-Sim provides a custom class creation method for `SimulationObject` that gives special meaning to specific methods and attributes.

Below, we define a simulation object class that models a random walk and illustrates the key features of `SimulationObject`.

```python
import random

class RandomWalkSimulationObject(de_sim.SimulationObject):
    " A 1D random walk model, with random delays between steps "

    def __init__(self, name):
        super().__init__(name)

    def init_before_run(self):
        " Initialize before a simulation run; called by the simulator "
        self.position = 0
        self.history = {'times': [0],
                        'positions': [0]}
        self.schedule_next_step()

    def schedule_next_step(self):
        " Schedule the next event, which is a step "
        # A step moves -1 or +1 with equal probability
        step_value = random.choice([-1, +1])
        # The time between steps is 1 or 2, with equal probability
        delay = random.choice([1, 2])
        # Schedule an event `delay` time units in the future
        # Schedule the event for this object
        # The event stores a `RandomStepMessage` containing `step_value`
        self.send_event(delay, self, RandomStepMessage(step_value))

    def handle_step_event(self, event):
        " Handle a step event "
        # Update the position and history
        self.position += event.message.step_value
        self.history['times'].append(self.time)
        self.history['positions'].append(self.position)
        self.schedule_next_step()

    # `event_handlers` contains pairs that map each event message class
    # received by this simulation object to the method that handles
    # the event message class
    event_handlers = [(RandomStepMessage, handle_step_event)]

    # messages_sent registers all message types sent by this object
    messages_sent = [RandomStepMessage]
```

Subclasses of `SimulationObject` must use the following methods and attributes to initialize themselves, schedule and handle events, and access the simulation's time.

* Methods:
    1. **`init_before_run`** (optional): immediately before a simulation run, after all of the simulation objects have been added to a simulator, the simulator calls each simulation object's `init_before_run` method. In this method, simulation objects can send initial events and perform other initializations. For example, in `RandomWalkSimulationObject`, `init_before_run` schedules the object's first event and initializes its position and history attributes.
    2. **`send_event`**: `send_event(delay, receiving_object, event_message)` schedules an event to occur `delay` time units in the future at simulation object `receiving_object`. `event_message` must be an `EventMessage` instance. An event can be scheduled for any simulation object in a simulation, including the object scheduling the event, as `RandomWalkSimulationObject` does.
The event will be executed at its scheduled simulation time by an event handler in the simulation object `receiving_object`.
The handler defines an `event` parameter. 
Its value will be the scheduled event, which contains `event_message` in its `message` attribute.
Object-oriented DES terminology often describes the event message as being sent by the sending object at the message's send time (the simulation time when the sending object schedules the event) and being received by the receiving object at the event's receive time (the simulation time when the event is executed). An event message can thus be viewed as a directed edge in simulation space-time from the pair (sending object, send time) to (receiving object, receive time), as illustrated in \autoref{fig:phold_space_time_plot}.
    3. **event handlers**: an event handler is a method that handles and executes a simulation event. Event handlers have the signature `event_handler(self, event)`, where `self` is the simulation object that handles (receives) the event, and `event` is a simulation event. A subclass of `SimulationObject` must define at least one event handler, as illustrated by `handle_step_event` in the example above.

* Attributes:
    1. **`event_handlers`**: a simulation object can receive arbitrarily many types of event messages, and implement arbitrarily many event handlers. The attribute `event_handlers` must contain an iterator over pairs that map each event message class received by a `SimulationObject` subclass to the event handler that handles the event message class. In the example above, `event_handlers` associates `RandomStepMessage` event messages with the `handle_step_event` event handler.
    2. **`messages_sent`**: the types of messages sent by a subclass of `SimulationObject` must be listed in `messages_sent`. It ensures that a simulation object doesn't send messages of the wrong `EventMessage` class.
    3. **`time`**: `time` is a read-only attribute that always equals the current simulation time in every simulation object. For example, a `RandomWalkSimulationObject` saves the value of `time` when recording its history.

3: Use classes created above to simulate a random walk.

The `de_sim.Simulator` class simulates models.
Its `add_object` method adds a simulation object to the simulator.
The `initialize` method, which calls each simulation object's `init_before_run` method, must be executed before a simulation starts.
At least one simulation object in a simulation must schedule an initial event--otherwise, the simulation cannot start.
More generally, a simulation with no events to execute will terminate.
A simulator’s `run` method simulates a model. It takes the maximum time of a simulation run, and several optional configuration arguments. More information is available in the DE-Sim API documentation at [https://docs.karrlab.org/de_sim](https://docs.karrlab.org/de_sim/source/de_sim.html#de_sim.simulator.Simulator.simulate).

The example below simulates a random walk for `max_time` time units and uses Matplotlib to visualize its trajectory (\autoref{fig:random_walk_trajectory}).

```python
# Create a simulator
simulator = de_sim.Simulator()

# Create a random walk simulation object and add it to the simulation
random_walk_sim_obj = RandomWalkSimulationObject('rand_walk')
simulator.add_object(random_walk_sim_obj)

# Initialize the simulation
# This executes `init_before_run` in `random_walk_sim_obj`
simulator.initialize()

# Run the simulation until time 10
max_time = 10
simulator.run(max_time)

# Plot the random walk
import matplotlib.pyplot as plt
plt.step(random_walk_sim_obj.history['times'],
         random_walk_sim_obj.history['positions']),
         where='post')
plt.xlabel('Time')
plt.ylabel('Position')
plt.show()
```

![**Trajectory of a simulated random walk on the integer number line.**
The source code for this simulation is available in the DE-Sim Git repository.
\label{fig:random_walk_trajectory}](random_walk_plot.pdf){ width=70% }

# Performance of DE-Sim

\autoref{fig:performance} illustrates the performance of DE-Sim simulating a cyclic messaging network over a range of network sizes. The messaging network is a ring of nodes. 
When any node handles an event, it schedules the same type of event for its forward neighbor with a one time-unit delay.
Each simulation is initialized by sending a message to each node at the first time-unit. 
The code for this performance test is available in the DE-Sim Git repository. A Jupyter notebook that runs the test is also available at [https://sandbox.karrlab.org/tree/de_sim](https://sandbox.karrlab.org/tree/de_sim/4.%20DE-Sim%20performance%20test.ipynb).

![**Performance of DE-Sim simulating a cyclic messaging network over a range of network sizes.** 
We executed each simulation for 100 time-units. Each statistic represents the average of three simulation runs in a Docker container running on a 2.9 GHz Intel Core i5 processor. 
\label{fig:performance}](performance.pdf)

# Case study: a multi-algorithmic simulator for whole-cell models implemented using DE-Sim

We are using DE-Sim to develop WC-Sim [@goldberg2020wc_sim], a multi-algorithmic simulator for whole-cell models [@karr2015principles; @goldberg2018emerging; @karr2012whole]. 
Whole-cell models that predict phenotype from genotype by representing all of the biochemical activity in a cell have great potential to help scientists elucidate the basis of cellular behavior, help bioengineers rationally design biosensors and biomachines, and help physicians personalize medicine.

Due to the diverse timescales of the subsystems inside cells, one promising way to simulate whole-cell models is to co-simulate slow subsystems with fined-grained algorithms and fast subsystems with coarse-grained algorithms. For example, slow subsystems, such as transcription, could be simulated with the Stochastic Simulation Algorithm (SSA, @gillespie1977exact), while faster subsystems, such as signal transduction, could be simulated with ordinary differential equations (ODEs). Metabolism, another fast process, could be simulated with dynamic Flux-Balance Analysis (dFBA, @orth2010flux; @mahadevan2002dynamic). However, there are no tools for co-simulating these algorithms beyond ad hoc implementations for specific models.

To accelerate whole-cell modeling, we are using DE-Sim to create WC-Sim.
First, we implemented a Python object that tracks the populations of the molecular species represented by a model. Second, we used pandas, NumPy, and ODES scikit [@malengier2018odes] to implement simulation object subclasses for dFBA, ODE, and SSA simulations. Third, we used event messages to schedule the execution of these simulation algorithms and coordinate their reading and updating of the species populations.

DE-Sim's OO functionality facilitated the implementation of classes for dFBA, ODE, and SSA, and DE-Sim's event messages streamlined the co-simulation these algorithms.
In addition, the ability to use NumPy made it easy to generate the random numbers needed to implement SSA, and the ability to use ODES scikit expedited the use of CVODE (@hindmarsh2005sundials) to implement the ODE simulation object class.
We anticipate that WC-Sim will help researchers conduct unprecedented simulations of cells.

# Conclusion

In summary, DE-Sim is an open-source, object-oriented, discrete-event simulation tool implemented in Python that makes it easier for modelers to create and simulate complex data-intensive models. First, DE-Sim enables researchers to conveniently use Python's OO features to manage multiple types of model components and their interactions. Second, DE-Sim enables researchers to directly use Python data science tools, such as pandas and SciPy, and large, heterogeneous datasets to calibrate complex models. Together, we anticipate that DE-Sim will accelerate the construction and simulation of unprecedented models of complex systems, leading to new scientific discoveries and engineering innovations.

To further advance the simulation of complex models, we aim to improve the simulation performance of DE-Sim. One potential direction is to use DE-Sim as a specification language for a parallel DES system such as ROSS [@carothers2000ross]. This combination of DE-Sim and ROSS would enable modelers to both create models with DE-Sim's high-level model specification semantics and quickly simulate complex models with ROSS.

# Availability of DE-Sim

DE-Sim is freely and openly available under the MIT license at the locations below.

* Python package: [PyPI: de-sim](https://pypi.org/project/de-sim/)
* Docker image: [Docker Hub: karrlab/de_sim](https://hub.docker.com/r/karrlab/de_sim)
* Tutorials: Jupyter notebooks at [https://sandbox.karrlab.org/tree/de_sim](https://sandbox.karrlab.org/tree/de_sim)
* Installation instructions and documentation of DE-Sim's API: [docs.karrlab.org](https://docs.karrlab.org/de_sim/)
* Issue tracker: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/issues/)
* Source code: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/)
* Guide to contributing to DE-Sim developers: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/blob/master/CONTRIBUTING.md/)
* Code of conduct for developers: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/blob/master/CODE_OF_CONDUCT.md)
* Continuous integration: [CircleCI: gh/KarrLab/de_sim](https://circleci.com/gh/KarrLab/de_sim/)

DE-Sim requires [Python](https://www.python.org/) 3.7 or higher and [pip](https://pip.pypa.io/).

This article discusses version 0.1.1 of DE-Sim.

# Acknowledgements

We thank Yin Hoon Chew for her helpful feedback. This work was supported by the National Science Foundation [1649014 to JRK], the National
Institutes of Health [R35GM119771 to JRK], and the Icahn Institute for Data Science and Genomic Technology.

# References
