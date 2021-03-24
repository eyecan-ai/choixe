import click


@click.command('check', help='Check Configuration file')
@click.option('-c', '--configuration_file', required=True, help="Input configuration file.")
@click.option('--close/--noclose', default=True, help="Raises system error if placeholders found")
def check(configuration_file, close):

    from choixe.configurations import XConfig
    import rich

    try:
        cfg = XConfig(filename=configuration_file)
        rich.print(cfg.to_dict())
    except Exception as e:
        rich.print(f"[red]Invalid configuration file: {e}[/red]")
        import sys
        sys.exit(1)

    rich.print("[green]Configuration is good![/green]")

    # d = cfg.to_dict(discard_private_qualifiers=False)
    cfg.check_available_placeholders(close_app=close)
