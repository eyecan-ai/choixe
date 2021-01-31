from click.testing import CliRunner
from choixe.cli.compile import compile
from pathlib import Path


def test_compile(sample_configurations_data, tmpdir):
    runner = CliRunner()

    for cfg_data in sample_configurations_data:
        filename = cfg_data['filename']
        has_placeholders = cfg_data['has_placeholders']

        outfile = Path(tmpdir) / f'_copy_{Path(filename).name}'

        if has_placeholders:
            result = runner.invoke(compile, ['-c', filename, '-o', outfile])
            assert result.exit_code == 1

            result = runner.invoke(compile, ['-c', filename, '-o', outfile, '--nocheck'])
            assert result.exit_code == 0
        else:
            result = runner.invoke(compile, ['-c', filename, '-o', outfile])
            assert result.exit_code == 0

            result = runner.invoke(compile, ['-c', filename, '-o', outfile, '--nocheck'])
            assert result.exit_code == 0
        # result = runner.invoke(check, ['-c', cfg_file, '--noclose'])
        # assert result.exit_code == 0
