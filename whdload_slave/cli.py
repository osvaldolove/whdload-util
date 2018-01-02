# -*- coding: utf-8 -*-
"""Console script for whdload_slave."""

import os
import click

from .whdload_slave import WHDLoadSlaveFile
from .whdload_display import WHDLoadDisplay


@click.command()
@click.argument(
    'path',
    type=click.Path(
        exists=True, readable=True, file_okay=True, resolve_path=True))
def main(path):
    """Console script for whdload_slave."""
    whdload_slave = WHDLoadSlaveFile.from_path(path)
    whdload_slave.read()
    display = WHDLoadDisplay(whdload_slave)

    click.echo(click.style('WHDLoad Slave Reader v0.1.0', fg='green'))
    click.echo('')
    for key, value in display.display_properties():
        click.echo(click.style(key, fg='yellow'), nl=False)
        click.echo(": {}".format(value))


if __name__ == '__main__':
    main()
