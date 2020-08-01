""" Test Jupyter notebooks

:Author: Jonathan Karr <karr@mssm.edu>
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-06-27
:Copyright: 2020, Karr Lab
:License: MIT
"""

import glob
import json
import nbconvert.preprocessors
import nbformat
import os
import unittest


@unittest.skipIf(os.getenv('CIRCLECI', '0') in ['1', 'true'], 'Jupyter server not setup in CircleCI')
class ExamplesTestCase(unittest.TestCase):
    TIMEOUT = 600

    """
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, 'examples')

    @classmethod
    def tearDownClass(cls):
        sys.path.remove('examples')

    def setUp(self):
        self.dirname = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dirname)
    """

    def test_jupyter(self):
        failed_notebooks = []
        for filename in glob.glob('de_sim/examples/jupyter_examples/*.ipynb'):
            with open(filename) as file:
                version = json.load(file)['nbformat']
            with open(filename) as file:
                notebook = nbformat.read(file, as_version=version)
            execute_preprocessor = nbconvert.preprocessors.ExecutePreprocessor(timeout=self.TIMEOUT)
            try:            
                execute_preprocessor.preprocess(notebook, {'metadata': {'path': 'de_sim/examples/jupyter_examples'}})
            except Exception as e:
                failed_notebooks.append(filename)
                print(e)

        if failed_notebooks:
            raise Exception('The following notebooks could not be executed:\n  {}'.format('\n  '.join(sorted(failed_notebooks))))
