from click.testing import CliRunner
from choixe.cli.check import check
from pathlib import Path


def test_check(sample_configurations_data):
    runner = CliRunner()

    for cfg_data in sample_configurations_data:
        filename = cfg_data['filename']
        has_placeholders = cfg_data['has_placeholders']

        result = runner.invoke(check, ['-c', filename])
        assert result.exit_code == (1 if has_placeholders else 0)

        result = runner.invoke(check, ['-c', filename, '--noclose'])
        assert result.exit_code == 0


def test_check_wrong(sample_configurations_data):
    runner = CliRunner()

    for cfg_data in sample_configurations_data:
        filename = Path(str(cfg_data['filename']) + "@IMPOSSIBLE_ST3ING!")
        has_placeholders = cfg_data['has_placeholders']
        print(has_placeholders)

        result = runner.invoke(check, ['-c', filename])
        assert result.exit_code == 1
