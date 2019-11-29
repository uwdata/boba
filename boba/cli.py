# -*- coding: utf-8 -*-

"""Console script."""
import click
import os
from .parser import Parser
from .__init__ import __version__


@click.command()
@click.option('--script', '-s', help='Path to template script',
              default='./template.py', show_default=True)
@click.option('--json', '-j', help='Path to JSON spec',
              default='./spec.json', show_default=True)
@click.option('--out', '-o', help='Output directory',
              default='.', show_default=True)
@click.option('--lang', '-l', help='Language, can be python/R [default: inferred from file extension]',
              default='')
def compile(script, json, out, lang):
    """Generate multiverse analysis from specifications."""

    check_path(script)
    check_path(json)

    click.echo('Creating multiverse from {} and {}'.format(script, json))
    ps = Parser(script, json, out, lang)
    ps.main()

    ex = """To execute the multiverse, run the following commands:
    cd {}
    sh execute.sh
    """.format(os.path.join(out, 'multiverse'))
    click.secho('Success!', fg='green')
    click.secho(ex, fg='green')


def check_path(p):
    """Check if the path exists"""
    if not os.path.exists(p):
        msg = 'Error: Path "{}" does not exist.'.format(p)
        print_help(msg)


def print_help(err=''):
    """Show help message and exit."""
    ctx = click.get_current_context()
    click.echo(ctx.get_help())

    if err:
        click.echo('\n' + err)
    ctx.exit()


@click.group()
@click.version_option()
def main():
    pass


main.add_command(compile)

if __name__ == "__main__":
    main()
