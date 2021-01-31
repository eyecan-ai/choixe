from click.testing import CliRunner
from choixe.cli.main import choixe


def test_cli(sample_configurations_data):
    runner = CliRunner()
    runner.invoke(choixe)
