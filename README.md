[//]: # ( [![PyPI package](https://img.shields.io/pypi/v/de_sim.svg)](https://pypi.python.org/pypi/de_sim) )
[![Documentation](https://readthedocs.org/projects/de_sim/badge/?version=latest)](https://docs.karrlab.org/de_sim)
[![Test results](https://circleci.com/gh/KarrLab/de_sim.svg?style=shield)](https://circleci.com/gh/KarrLab/de_sim)
[![Test coverage](https://coveralls.io/repos/github/KarrLab/de_sim/badge.svg)](https://coveralls.io/github/KarrLab/de_sim)
[![Code analysis](https://api.codeclimate.com/v1/badges/2fa3ece22f571fd36b12/maintainability)](https://codeclimate.com/github/KarrLab/de_sim)
[![License](https://img.shields.io/github/license/KarrLab/de_sim.svg)](LICENSE)
![Analytics](https://ga-beacon.appspot.com/UA-86759801-1/de_sim/README.md?pixel)

# DE-Sim

`DE-Sim` provides an object-oriented discrete event simulation
tool for Python that's similar to Simula.
Simulation logical processes are objects and they schedule
simulation events by exchanging messages.
Simulation applications are composed of multiple
subclasses of `SimulationObject`.

## Installation
1. Install dependencies
    
    * Python >= 3.7
    * pip >= 19

2. Install this package 

    * Install latest release from PyPI
      ```
      de_sim
      ```

    * Install latest revision from GitHub
      ```
      pip install git+https://github.com/KarrLab/de_sim.git#egg=de_sim
      ```

## API documentation
Please see the [API documentation](https://docs.karrlab.org/de_sim).

## License
The package is released under the [MIT license](LICENSE).

## Contributing to `DE-Sim`
We enthusiastically welcome contributions to `DE-Sim`! Please see the [guide to contributing](CONTRIBUTING.md) and the [developer's code of conduct](CODE_OF_CONDUCT.md).

## Development team
This package was developed by the [Karr Lab](https://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai in New York, USA by the following individuals:

* [Arthur Goldberg](https://www.mountsinai.org/profiles/arthur-p-goldberg)
* [Jonathan Karr](https://www.karrlab.org)

## Acknowledgements
This work was supported by National Science Foundation award 1649014 and National Institutes of Health award R35GM119771.

## Questions and comments
Please submit questions and issues to [GitHub](https://github.com/KarrLab/de_sim/issues) or contact the [Karr Lab](mailto:info@karrlab.org).
