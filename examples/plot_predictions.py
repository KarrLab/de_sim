#!/usr/bin/env python3
""" Plot DataFrame of simulation checkpoint series

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-05-15
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

import pandas
import argparse
import sys
import matplotlib.pyplot as plt

def parse_args(cli_args):
    """ Parse command line arguments

    Returns:
        :obj:`argparse.Namespace`: parsed command line arguements
    """
    parser = argparse.ArgumentParser(description="Plot multialgorithmic simulation results from dataframe")
    parser.add_argument('dataframe_file', type=str,
        help="HDF5 file containing multialgorithmic simulation results in a dataframe")
    args = parser.parse_args(cli_args)
    return args

def plot(args):
    store = pandas.HDFStore(args.dataframe_file)
    predictions = store.get('dataframe')
    predictions.plot()
    plt.show()
    store.close()

def main():
    args = parse_args(sys.argv[1:])
    plot(args)

if __name__ == '__main__':  # pragma: no cover     # run from the command line
    try:
        main()
    except KeyboardInterrupt:
        pass
