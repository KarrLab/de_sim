---
title: 'DE-Sim: an object-oriented discrete-event simulation tool for complex, data-driven modeling'
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

Recent advances in data collection and storage have created unprecedented opportunities to gain insights into complex systems such as the biochemical networks that generate cellular behavior. Deciphering this data will likely require larger and more comprehensive models derived from a combination of first principles and large datasets. One of the most promising methods for building and simulating large, data-driven models is discrete-event simulation (DES). However, it is difficult to use large, heterogeneous datasets to build DES models because the existing DES tools are siloed from popular data science tools such as pandas. To make it easier to construct and simulate large, data-driven models, we developed DE-Sim ([https://github.com/KarrLab/de_sim](https://github.com/KarrLab/de_sim)), an open-source, Python-based object-oriented DES tool. Because DE-Sim is implemented in Python, DE-Sim makes it easy to use high-level data science tools such as NumPy, pandas, SciPy, and SQLAlchemy to build complex models and analyze the results of their simulations. We anticipate the DE-Sim will enable a new generation of models that capture systems with unprecedented breadth and depth. DE-Sim is already being used to develop a hybrid simulation tool for whole-cell models that predict phenotype from genotype by capturing all of the biochemical activity in a cell.

# Introduction: Need for tools for building and simulating complex, data-driven models

A central challenge in science is to understand how systems behaviors emerge from complex networks. For example, systems biology seeks to understand how cellular phenotypes emerge from complex biochemical networks and systems neuroscience aims to understand how cognition arises from neural networks. Due to recent advances in data collection and storage, many scientific fields now have extensive and detailed data about a wide range of networks. Larger and more comprehensive models, such as models of entire cells and brains, are needed to decipher this data. However, it remains difficult to use build and simulate complex models.

One of the most promising methods for simulating large models is discrete-event simulation (DES). DES represents a system as a collection of processes that can read the values of a set of shared variables and schedule events to modify their values at discrete instants in time. DES is ideal for large models because its discrete structure is conducive to parallel execution. For example, Barnes et al. have executed DES models using nearly 2 million cores [@Barnes2013]. Several DES tools are available, including basic tools such as SimPy [@matloff2008introduction] which enable scientists to implement models using functional programming; high-performance, parallelized, object-oriented tools such as POSE [@wilmarth2005pose] and ROSS [@carothers2002ross] which support C-based models; and commercial tools such as Simula8 [@concannon2003dynamic] which provide proprietary languages for describing models. DES has been applied to a wide range of models. For example, epidemiologists have used DES to simulate the transmission of infectious disease, computer engineers have used DES to simulate distributed computer networks, and the military often uses DES to simulate wars [@banks2005discrete]. However, it remains challenging to use large, heterogeneous datasets to build DES models. It is difficult to implement complex models using functional DES tools such as SimPy, and the C-based DES tools, such as POSE and ROSS, are siloed from popular data science tools such as pandas [@mckinney2010data].

To make it easier to construct and simulate complex, data-driven models, we developed DE-Sim, an open-source, Python-based object-oriented DES tool. Because DE-Sim is implemented in Python, DE-Sim makes it easy to use high-level data science tools such as NumPy [@oliphant2006guide], pandas, SciPy [@virtanen2020scipy], and SQLAlchemy [@bayer2020sqlalchemy] to build models and analyze the results of their simulations. We have extensively tested and documented DE-Sim. As described below, DE-Sim is freely available from GitHub and PyPI.

Here, we outline the features of DE-Sim, provide a brief tutorial of building and simulating models with DE-Sim, analyze the performance of DE-Sim, summarize how DE-Sim is already enabling WC-Sim [@goldberg2020wc_sim], a hybrid simulator for whole-cell models [@karr2015principles; @goldberg2018emerging; @karr2012whole], and describe the advantages of DE-Sim over existing DES tools. Additional examples, tutorials, installation instructions, and source code documentation are available at [https://github.com/KarrLab/de_sim](https://github.com/KarrLab/de_sim).

# Key features of DE-Sim

To help users build and simulate complex, data-driven models, DE-Sim provides the following features:

* **High-level, object-oriented modeling:** DE-Sim makes it easy for researchers to use object-oriented Python programming to build models. This makes it easy to use large, heterogeneous datasets and high-level data science packages such as NumPy, pandas, SciPy, and SQLAlchemy to build complex models.
* **Powerful stop conditions:** DE-Sim makes it easy to implement complex stop conditions. Stop conditions can be implemented as simple Python functions that return true when the simulation state reaches the desired stop condition.
* **Simple simulation logging:** DE-Sim provides tools for recording the results of simulations, as well as metadata such as the start and run time of each simulation.
* **Space-time visualizations for analysis and debugging:** DE-Sim can generate space-time visualizations of simulation trajectories (\autoref{fig:phold_space_time_plot}). These diagrams are valuable tools for understanding and debugging models.
* **Checkpointing for restarting and debugging:** DE-Sim can checkpoint the state of simulations. These checkpoints can be used to restart or debug simulations. Checkpointing is particularly helpful for using DE-Sim on clusters that have short time limits, or for using DE-Sim on spot-priced virtual machines in commercial clouds.

![**DE-Sim can generate space-time visualizations of simulation trajectories.** 
This figure illustrates a space-time visualization of all of the events and messages in simulation of the parallel hold (PHOLD) DES benchmark model [@fujimoto1990performance] with three simulation objects. The timeline (grey line) for each object shows its events (grey dots). The event messages (arrows) show the message which triggered each event and the message generated by each event. The curved blue arrows indicate self messages to the same simulation object and the straight purple arrows indicate messages to other simulation objects. The source code for the model is available in the DE-Sim Git repository. 
\label{fig:phold_space_time_plot}](phold_space_time_plot.pdf)

# Tutorial: Building and simulating models with DE-Sim

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

# Performance of DE-Sim

DE-Sim achieves good performance by using Python's `heapq` priority queue package to schedule events.
\autoref{fig:performance} shows the performance of DE-Sim simulating a model of a cyclic messaging network over range of network sizes.

![**Performance of DE-Sim simulating a model of a cyclic messaging network over a range of network sizes.** Each statistic represents the average of three executions in a Docker container on a 2.9 GHz Intel Core i5 processor. The source code for the cyclic messaging network model is available in the DE-Sim Git repository.
\label{fig:performance}](performance.pdf)

# Case study: hybrid simulation tool for whole-cell modeling

We have used DE-Sim to develop WC-Sim [@goldberg2020wc_sim], a hybrid simulation tool for whole-cell models [@karr2015principles; @goldberg2018emerging; @karr2012whole]. Whole-cell models which predict phenotype from genotype by representing all of the biochemical activity in a cell have great potential to help scientists elucidate the basis of cellular behavior, help bioengineers rationally design biosensors and biomachines, and help physicians personalize medicine.

Due to the diverse timescales of the reactions inside cells, one promising way to build whole-cell models is to combine fine-grain submodels of slow processes, such as transcription, that are simulated with the Stochastic Simulation Algorithm (SSA, @gillespie1977exact) with medium-grain submodels of faster processes, such as signal transduction, that are simulated with ordinary differential equations (ODEs) and coarse-grained submodels of fast processes, such as metabolism, that are simulated with flux-balance analysis (FBA, @orth2010flux). This requires co-simulating SSA, FBA, and other simulation algorithms. However, there are no tools for co-simulating these algorithms.

To accelerate whole-cell modeling, we have used DE-Sim to implement WC-Sim [@goldberg2020wc_sim], a hybrid simulation tool for whole-cell models described in the WC-Lang language [@karr2020wc_lang]. We implemented WC-Sim by using DE-Sim to implement logical processes for SSA, ODE, and FBA simulations and event messages for synchronizing the counts of species shared among submodels, and developing custom codes to translate models described with WC-Lang into instances of SSA, ODE, and FBA simulation objects. DE-Sim made it easy develop WC-Sim by enabling us to use the WC-Lang Python package to translate models into DES objects and enabling us to use Python packages for ODE and FBA simulation to implement the simulation classes. This reduced the amount of effort that would have otherwise been required to implement WC-Sim. We anticipate the WC-Sim will enable researchers to conduct unprecedented models of cellular biochemistry.

# Comparison of DE-Sim with other DES tools

* Low-level tools in high-level languages
  * SimPy [@matloff2008introduction]
* High-level, low-performance C-based tool
  * SystemC [@mueller2001simulation]
* High-performance C-based tools
  * POSE [@wilmarth2005pose]
  * ROSS [@carothers2002ross]
* Commercial tools with proprietary modeling languages
  * Simul8 [@concannon2003dynamic]

![**Strengths and weakness of DE-Sim compared to other DES tools.** 
\label{fig:comparison}](comparison.pdf)

# Availability of DE-Sim

DE-Sim is freely and openly available under the MIT license at the locations below.

* Python package: [PyPI: de-sim](https://pypi.org/project/de-sim/)
* Docker image: [DockerHub: karrlab/de_sim](https://hub.docker.com/r/karrlab/de_sim)
* Examples, tutorials, and documentation: [docs.karrlab.org](https://docs.karrlab.org/de_sim/)
* Issue tracker: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/issues/)
* Source code: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/)
* Guide to contributing and code of conduct: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/)
* Continuous integration: [CircleCI: gh/KarrLab/de_sim](http://circleci.com/gh/KarrLab/de_sim/)

DE-Sim requires [Python](https://www.python.org/) 3.6 or higher and [pip](https://pip.pypa.io/).

This article discusses version 0.0.3 of DE-Sim.

# Acknowledgements

This worked was supported by the National Science Foundation [award 1649014 to J.R.K.], the National
Institutes of Health [award R35GM119771 to J.R.K], and the Icahn Institute for Data Science and Genomic Technology.

# References
