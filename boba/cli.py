# -*- coding: utf-8 -*-

"""Console script."""
import click
import os
from .parser import Parser


@click.command()
@click.option('--script', help='Path to your template script.')
@click.option('--json', help='Path to your JSON spec.')
@click.option('--out', default='.', help='Output directory.')
def main(script, json, out):
    """Generate multiverse analysis from specifications."""
    script = check_path(script, 'script_annotated.py')
    json = check_path(json, 'spec.json')

    click.echo('Creating multiverse from {} and {}'.format(script, json))
    ps = Parser(script, json, out)
    ps.main()

    ex = """To execute the multiverse, run the following commands:
    cd {}
    sh execute.sh
    """.format(os.path.join(out, 'multiverse'))
    click.echo('Success!')
    click.echo(ex)


def check_path(p, default):
    """If path is not provided and default exists, use default"""
    if not p:
        if os.path.exists(default):
            return default
        else:
            print_help()
    elif not os.path.exists(p):
        click.echo('Error: Path "" does not exist.'.format(p))


def print_help():
    """Show help message and exit."""
    ctx = click.get_current_context()
    click.echo(ctx.get_help())
    ctx.exit()


if __name__ == "__main__":
    main()
