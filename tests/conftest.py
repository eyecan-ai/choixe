import pytest
import os
from pathlib import Path


@pytest.fixture(scope='session')
def data_folder():
    dirname = os.path.dirname(__file__)
    return os.path.join(dirname, 'sample_data')


@pytest.fixture(scope='session')
def sample_configurations_data(data_folder):
    configurations_folder = Path(data_folder) / 'configurations'
    return [
        {
            'filename': configurations_folder / 'sample_yaml' / 'main.yaml',
            'has_placeholders': True
        },
        {
            'filename': configurations_folder / 'sample_yaml' / 'main_single.yaml',
            'has_placeholders': True
        },
        {
            'filename': configurations_folder / 'single_yaml' / 'main_noplaceholders.yaml',
            'has_placeholders': False
        },
        {
            'filename': configurations_folder / 'single_yaml' / 'main.yaml',
            'has_placeholders': True,
            'to_replace': {  # If to_replace is set, it has to contain all placeholders!
                'one': 1,
                'four': 33,
                'three.t31': True,
                'three.name': 'hello'
            }
        }
    ]
