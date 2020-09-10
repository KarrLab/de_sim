[![PyPI package](https://img.shields.io/pypi/v/de_sim.svg)](https://pypi.python.org/pypi/de_sim)
[![Documentation](https://readthedocs.org/projects/de_sim/badge/?version=latest)](https://docs.karrlab.org/de_sim)
[![Test results](https://circleci.com/gh/KarrLab/de_sim.svg?style=shield)](https://circleci.com/gh/KarrLab/de_sim)
[![Test coverage](https://coveralls.io/repos/github/KarrLab/de_sim/badge.svg)](https://coveralls.io/github/KarrLab/de_sim)
[![Code analysis](https://api.codeclimate.com/v1/badges/2fa3ece22f571fd36b12/maintainability)](https://codeclimate.com/github/KarrLab/de_sim)
[![License](https://img.shields.io/github/license/KarrLab/de_sim.svg)](LICENSE)
![Analytics](https://ga-beacon.appspot.com/UA-86759801-1/de_sim/README.md?pixel)

# *DE-Sim*: a Python-based object-oriented discrete-event simulator for modeling complex systems

*DE-Sim* is an open-source, Python-based object-oriented discrete-event simulation (DES) tool that makes it easy to use large, heterogeneous datasets and high-level data science tools such as [NumPy](https://numpy.org/), [Scipy](https://scipy.org/scipylib/index.html), [pandas](https://pandas.pydata.org/), and [SQLAlchemy](https://www.sqlalchemy.org/) to build and simulate complex computational models. Similar to [Simula](http://www.simula67.info/), *DE-Sim* models are implemented by defining logical process objects which read the values of a set of shared variables and schedule events to modify their values at discrete instants in time.

To help users build and simulate complex, data-driven models, *DE-Sim* provides the following features:

* **High-level, object-oriented modeling:** *DE-Sim* makes it easy for users to use object-oriented Python programming to build models. This makes it easy to use large, heterogeneous datasets and high-level data science packages such as NumPy, pandas, SciPy, and SQLAlchemy to build complex models.
* **Powerful stop conditions:** *DE-Sim* makes it easy to implement complex stop conditions. Stop conditions can be implemented as simple Python functions that return true when the simulation state reaches the desired stop condition.
* **Simple simulation logging:** *DE-Sim* provides tools for recording the results of simulations, as well as metadata such as the start and run time of each simulation.
* **Space-time visualizations for analysis and debugging:** *DE-Sim* can generate space-time visualizations of simulation trajectories. These diagrams are valuable tools for understanding and debugging models.
* **Checkpointing for restarting and debugging:** *DE-Sim* can checkpoint the state of simulations. These checkpoints can be used to restart or debug simulations. Checkpointing is particularly helpful for using *DE-Sim* on clusters that have short time limits, or for using *DE-Sim* on spot-priced virtual machines in commercial clouds.

## Projects that use *DE-Sim*
*DE-Sim* has been used to develop [WC-Sim](https://github.com/KarrLab/wc_sim), a multi-algorithmic simulator for [whole-cell models](https://www.wholecell.org).

## Examples
* [Minimal simulation](de_sim/examples/minimal_simulation.py): a minimal example of a simulation
* [Random walk](de_sim/examples/random_walk.py): a random one-dimensional walk which increments or decrements a variable with equal probability at each event
* [Parallel hold (PHOLD)](de_sim/examples/phold.py): model developed by Richard Fujimoto for benchmarking parallel DES simulators
* [Epidemic](https://github.com/KarrLab/de_sim/blob/master/de_sim/examples/sirs.py): an SIR model of an epidemic of an infectious disease

## Tutorial
Please see [sandbox.karrlab.org](https://sandbox.karrlab.org/tree/de_sim) for interactive tutorials on creating and executing models with *DE-Sim*.

## Template for models and simulations
[`de_sim/examples/minimal_simulation.py`](de_sim/examples/minimal_simulation.py) contains a template for implementing and simulating a model with *DE-Sim*.

## Installation
1. Install dependencies
    
    * Python >= 3.7
    * pip >= 19

2. Install this package 

    * Install latest release from PyPI
      ```
      pip install de_sim
      ```

    * Install a Docker image with the latest release from DockerHub
      ```
      docker pull karrlab/de_sim
      ```

    * Install latest revision from GitHub
      ```
      pip install git+https://github.com/KarrLab/de_sim.git#egg=de_sim
      ```

## API documentation
Please see the [API documentation](https://docs.karrlab.org/de_sim/source/de_sim.html).

## Performance
Please see the [*DE-Sim* article](joss_paper/paper.md) for information about the performance of *DE-Sim*.

## Strengths and weaknesses compared to other DES tools
Please see the [*DE-Sim* article](joss_paper/paper.md) for a comparison of *DE-Sim* with other DES tools.

## License
The package is released under the [MIT license](LICENSE).

## Citing *DE-Sim*
Please use the following reference to cite *DE-Sim*:

Arthur P. Goldberg & Jonathan Karr. DE-Sim: an object-oriented, discrete-event simulation tool for data-intensive modeling of complex systems in Python. In preparation.

## Contributing to *DE-Sim*
We enthusiastically welcome contributions to *DE-Sim*! Please see the [guide to contributing](CONTRIBUTING.md) and the [developer's code of conduct](CODE_OF_CONDUCT.md).

## Development team
This package was developed by the [Karr Lab](https://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai in New York, USA by the following individuals:

* [Arthur Goldberg](https://www.mountsinai.org/profiles/arthur-p-goldberg)
* [Jonathan Karr](https://www.karrlab.org)

## Acknowledgements
This work was supported by National Science Foundation award 1649014, National Institutes of Health award R35GM119771, and the Icahn Institute for Data Science and Genomic Technology.

## Questions and comments
Please submit questions and issues to [GitHub](https://github.com/KarrLab/de_sim/issues) or contact the [Karr Lab](mailto:info@karrlab.org).
