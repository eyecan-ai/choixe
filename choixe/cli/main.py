import click
from choixe.cli.check import check
from choixe.cli.compile import compile


@click.group()
def choixe():
    pass


choixe.add_command(check)
choixe.add_command(compile)
