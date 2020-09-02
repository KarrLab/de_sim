""" Utilities for testing

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-05-16
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""


def make_args(args_dict, required, options):
    """ Make command line argument list, for testing argument parsers

    Args:
        args_dict (:obj:`dict`): argument names and their values
        required (:obj:`list`): required command line arguments
        options (:obj:`list`): optional command line arguments

    Returns:
        :obj:`list`: list of strings in command line arguments, as would appear in `sys.argv[1:]`
    """
    args = []
    for opt in options:
        if opt in args_dict:
            args.append('--' + opt)
            args.append(str(args_dict[opt]))
    for arg in required:
        args.extend([str(args_dict[arg])])
    return args
