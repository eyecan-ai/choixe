import pytest
import os
from pathlib import Path


def pytest_addoption(parser):
    parser.addoption("--rabbitmq", action="store_true",
                     help="run the tests only in case of rabbitmq server active")


def pytest_runtest_setup(item):
    if 'rabbitmq' in item.keywords and not item.config.getoption("--rabbitmq"):
        pytest.skip("need --rabbitmq for full testing with rabbitmq server")


@pytest.fixture(scope='session')
def data_folder():
    dirname = os.path.dirname(__file__)
    return os.path.join(dirname, 'sample_data')


@pytest.fixture(scope='function')
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
