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
Furthermore, complex models that represent multiple types of components and their interactions will require diverse approximations and large, heterogeneous datasets. New tools are needed to build and simulate such data-intensive models.

One of the most promising methods for building and simulating data-intensive models is discrete-event simulation (DES). DES represents the dynamics of a system as a sequence of instantaneous events [@fishman2013discrete]. DES is used for a wide range of research, such as studying the dynamics of biochemical networks, characterizing the performance of computer networks, evaluating potential war strategies, and forecasting epidemics [@banks2005discrete].
Although multiple DES tools exist, it remains difficult to build and simulate data-intensive models.  First, it is cumbersome to create complex models with the low-level languages supported by many of the existing tools. Second, most of the existing tools are siloed from the ecosystems of data science tools that are exploding around Python and R.

To address this problem, we developed DE-Sim ([https://github.com/KarrLab/de_sim](https://github.com/KarrLab/de_sim)), an open-source, object-oriented (OO), Python-based DES tool.
DE-Sim helps researchers model complex systems by enabling them to use Python's powerful OO features to manage multiple types of components and multiple types of interactions.
By building upon Python, DE-Sim also makes it easy for researchers to use Python's powerful data science tools, such as pandas [@mckinney2010data] and SciPy [@virtanen2020scipy], to incorporate large, heterogeneous datasets into comprehensive and detailed models.
We anticipate that DE-Sim will enable a new generation of models that capture systems with unprecedented breadth and depth.
For example, we are using DE-Sim to develop WC-Sim [@goldberg2020wc_sim], a multi-algorithmic simulation tool for whole-cell models [@karr2015principles; @goldberg2018emerging; @karr2012whole; @goldberg2016toward] that predict phenotype from genotype by capturing all of the biochemical activity in a cell.

Here, we describe the need for new tools for building and simulating more comprehensive and more detailed models, and outline how DE-Sim addresses this need. In addition, we summarize the strengths of DE-Sim over existing DES tools, and we report the simulation performance of DE-Sim. Finally, we outline our plans to increase the performance of simulations executed by DE-Sim. 
A tutorial that describes how to build and simulate models with DE-Sim, examples, and documentation are available online, as described in the 'Availability of DE-Sim' section below.

# Statement of Need

Many scientific fields can now collect detailed data about the components of complex systems and their interactions. For example, deep sequencing has dramatically increased the availability of molecular data about biochemical networks. Combined with advances in computing, we believe that it is now possible to use this data and first principles to create comprehensive and detailed models that can provide new insights into complex systems. For example, deep sequencing and other molecular data can be used to build whole-cell models.

Achieving such comprehensive and detailed models will likely require integrating disparate principles and diverse data. While there are several DES tools, such as SimEvents [@clune2006discrete] and SimPy [@matloff2008introduction], and numerous tools for working with large, heterogeneous datasets, such as pandas and SQLAlchemy [@bayer2020sqlalchemy], it is difficult to use these tools in combination. As a result, despite having all of the major ingredients, it remains difficult to build and simulate data-intensive models.

# DE-Sim provides critical features for building and simulating data-intensive models

DE-Sim simplifies the construction and simulation of *discrete-event models* through several features. First, DE-Sim structures discrete-event models as OO programs [@zeigler1987hierarchical]. This structure enables researchers to use classes of *simulation objects* to encapsulate the complex logic required to represent each *model component*, and use classes of *event messages* to encapsulate the logic required to describe their *interactions*. With DE-Sim, users define classes of simulation objects by creating subclasses of DE-Sim's simulation object class. DE-Sim simulation object classes can exploit all the features of Python classes. For example, users can encode relationships between the types of components in a model into hierarchies of subclasses of simulation objects. As a concrete example, a model of the biochemistry of RNA transcription and protein translation could be implemented using a superclass that captures the behavior of polymers and three subclasses that represent the specific properties of DNAs, RNAs, and proteins. DE-Sim makes it easy to model complex systems that contain multiple types of components through multiple classes of simulation objects. Users can model arbitrarily many instances of each type of component by creating multiple instances of the corresponding simulation object class. 

Second, by building on top of Python, DE-Sim makes it easy for researchers to use Python's extensive suite of data science tools to build models from heterogeneous, multidimensional datasets. For example, researchers can use tools such as H5py, ObjTables [@karr2020objtables], pandas, requests, and SQLAlchemy to retrieve diverse data from spreadsheets, HDF5 files, REST APIs, databases, and other sources; use tools such as NumPy [@oliphant2006guide] to integrate this data into a unified model; and use tools such as SciPy to perform calculations during simulations of models. DE-Sim also facilitates use of Python tools to analyze simulation results.

DE-Sim also provides several features to help users execute, analyze, and debug simulations:

* **Stop conditions:** DE-Sim makes it easy to terminate simulations when specific criteria are reached. Researchers can specify stop conditions as functions that return true when the simulation should conclude.
* **Results checkpointing:** DE-Sim makes it easy to record the results of simulations through an easily-configurable checkpointing module.
* **Space-time visualizations:** DE-Sim can generate space-time visualizations of simulation trajectories (\autoref{fig:phold_space_time_plot}). These diagrams can help researchers understand and debug simulations.
* **Reproducible simulations:** To help researchers debug simulations, repeated executions of the same simulation with the same configuration and same random number generator seed produce the same results.

![**DE-Sim can generate space-time visualizations of simulation trajectories.** 
This figure illustrates a space-time visualization of all of the events and messages in a simulation of the parallel hold (PHOLD) DES benchmark model [@fujimoto1990performance] with three simulation objects. The timeline (black line) for each object shows its events (grey dots). The blue and purple arrows illustrate events scheduled by simulation objects for themselves and other objects, respectively. The code for this simulation is available in the DE-Sim Git repository. 
\label{fig:phold_space_time_plot}](figures/phold_space_time_plot.png)

Together, we believe that these features can simplify and accelerate the development of complex, data-intensive models.

# Comparison of DE-Sim with existing discrete-event simulation tools

Although there are several other DES tools, we believe that DE-Sim uniquely facilitates data-intensive modeling through a novel combination of OO modeling and support for numerous high-level data science tools. \autoref{fig:comparison} compares the features and characteristics of DE-Sim with some of the most popular DES tools.

![**Comparison of DE-Sim with some of the most popular DES tools.**
DE-Sim is the only open-source, OO DES tool based on Python.
This combination of features makes DE-Sim uniquely suitable for creating and simulating complex, data-intensive models. 
\label{fig:comparison}](figures/comparison.png)

SimPy is an open-source DES tool that enables users to use functions to create simulation processes (SimPy's analog to DE-Sim's simulation objects). As another Python-based tool, SymPy also makes it easy for researchers to leverage the Python ecosystem to build models. However, we believe that DE-Sim makes it easier for researchers to build complex models by enabling them to implement models as collections of classes rather than collections of functions. In addition, we believe that DE-Sim is simpler to use because DE-Sim supports a uniform approach for scheduling events, whereas SimPy simulation processes must use two different approaches: one to schedule events for themselves, and another to schedule events for other processes.

SimEvents is a library for DES within the MATLAB/Simulink environment. While SimEvents' graphical interface makes it easy to create simple models, we believe that DE-Sim makes it easier to implement more complex models. By making it easy to use a variety of Python-based data science tools, DE-Sim makes it easier to use data to create models than SimEvents, which builds on a more limited ecosystem of data science tools.

SystemC is a `C++`-based OO DES tool that is frequently used to model digital systems [@mueller2001simulation]. While SystemC provides many of the same core features as DE-Sim, we believe that DE-Sim is more accessible to researchers than SystemC because DE-Sim builds upon Python, which is more popular than `C++` in many fields of research.

SIMSCRIPT III [@rice2005simscript] and SIMUL8 [@concannon2003dynamic] are commercial DES tools that enable researchers to implement models using proprietary languages. SIMSCRIPT III is well-suited to modeling decision support systems for domains such as war-gaming, communications networks, transportation, and manufacturing, and SIMUL8 is well-suited to modeling business processes. However, we believe that DE-Sim is more powerful for most scientific and engineering fields because DE-Sim can leverage Python's robust ecosystem of data science packages.

# Performance of DE-Sim

\autoref{fig:performance} illustrates the performance of DE-Sim simulating cyclic messaging networks over a range of network sizes. Each messaging network consists of a ring of nodes. 
When a node handles an event, it schedules the same type of event for its forward neighbor with a one time-unit delay.
Each simulation is initialized by sending a message to each node at the first time-unit. 
The code for this performance test is available in the DE-Sim Git repository, and in a Jupyter notebook at [https://sandbox.karrlab.org/tree/de_sim](https://sandbox.karrlab.org/tree/de_sim/4.%20DE-Sim%20performance%20test.ipynb).

![**Performance of DE-Sim simulating a range of sizes of a cyclic messaging network.** 
We executed each simulation for 100 time-units. Each statistic represents the average of three simulation runs in a Docker container running on a 2.9 GHz Intel Core i5 processor. 
\label{fig:performance}](figures/performance.png)

# Conclusion

In summary, DE-Sim is an open-source, object-oriented, discrete-event simulation tool implemented in Python that makes it easier for modelers to create and simulate complex, data-intensive models. First, DE-Sim enables researchers to conveniently use Python's OO features to manage multiple types of model components and their interactions. Second, DE-Sim enables researchers to directly use Python data science tools, such as pandas and SciPy, and large, heterogeneous datasets to construct models. Together, we anticipate that DE-Sim will accelerate the construction and simulation of unprecedented models of complex systems, leading to new scientific discoveries and engineering innovations.

To further advance the simulation of data-intensive models, we aim to improve the simulation performance of DE-Sim. One potential direction is to use DE-Sim as a specification language for a parallel DES system such as ROSS [@carothers2000ross]. This combination of DE-Sim and ROSS would enable modelers to both create models with DE-Sim's high-level model specification semantics and quickly simulate models with ROSS.

# Availability of DE-Sim

DE-Sim is freely and openly available under the MIT license at the locations below.

* Repository: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/)
* Jupyter notebook tutorials: [https://sandbox.karrlab.org/tree/de_sim](https://sandbox.karrlab.org/tree/de_sim)
* Documentation: [docs.karrlab.org](https://docs.karrlab.org/de_sim/)

DE-Sim requires [Python](https://www.python.org/) 3.7 or higher and [pip](https://pip.pypa.io/). This article discusses version 0.1.8 of DE-Sim.

# Acknowledgements

We thank Yin Hoon Chew for her helpful feedback. This work was supported by the National Science Foundation [1649014 to JRK], the National
Institutes of Health [R35GM119771 to JRK], and the Icahn Institute for Data Science and Genomic Technology.

# References

