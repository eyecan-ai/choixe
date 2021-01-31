from typing import Sequence, Tuple
import click


@click.command('compile', help='Compile Configuration file')
@click.option('-c', '--configuration_file', required=True, help="Input configuration file.")
@click.option('-o', '--output_file', required=True, help="Output single configuration file.")
@click.option('--check/--nocheck', default=True, type=bool, help="If flag is TRUE compile procedure will stop if placeholders found.")
@click.option('--option', 'options', multiple=True, nargs=2, help='Bind dataset name to underfolder path')
def compile(configuration_file: str, output_file: str, check: bool, options: Sequence[Tuple[str, str]]):

    from choixe.configurations import XConfig
    import rich

    try:
        cfg = XConfig(filename=configuration_file)
    except Exception as e:
        rich.print(f"[red]Invalid configuration file: {e}[/red]")
        import sys
        sys.exit(1)

    placeholders = cfg.available_placeholders()
    for key, value in options:
        if key in placeholders:
            placeholder = placeholders[key]
            cfg.deep_set(key, placeholder.cast(value))

    if check:
        cfg.check_available_placeholders(close_app=True)

    cfg.save_to(output_file)
