from click.testing import CliRunner
from choixe.cli.compile import compile
from pathlib import Path


def test_compile(sample_configurations_data, tmpdir):
    runner = CliRunner()

    for cfg_data in sample_configurations_data:
        filename = cfg_data['filename']
        has_placeholders = cfg_data['has_placeholders']
        to_replace = cfg_data['to_replace'] if 'to_replace' in cfg_data else []

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

        if len(to_replace) > 0 and has_placeholders:
            args = ['-c', filename, '-o', outfile]
            for k, v in to_replace.items():
                args += ['--option', k, v]
            result = runner.invoke(compile, args)
            assert result.exit_code == 0

        # result = runner.invoke(check, ['-c', cfg_file, '--noclose'])
        # assert result.exit_code == 0


def test_compile_wrong(sample_configurations_data, tmpdir):
    runner = CliRunner()

    for cfg_data in sample_configurations_data:
        filename = Path(str(cfg_data['filename']) + "@IMPOSSIBLE_ST3ING!")
        has_placeholders = cfg_data['has_placeholders']
        print(has_placeholders)

        outfile = Path(tmpdir) / f'_copy_{Path(filename).name}'

        result = runner.invoke(compile, ['-c', filename, '-o', outfile])
        assert result.exit_code == 1
