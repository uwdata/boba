# -*- coding: utf-8 -*-

"""Console script."""
import click
import os
from .parser import Parser


@click.command()
@click.option('--script', '-s', help='Path to template script',
              default='./script_annotated.py', show_default=True)
@click.option('--json', '-j', help='Path to JSON spec',
              default='./spec.json', show_default=True)
@click.option('--out', '-o', help='Output directory',
              default='.', show_default=True)
@click.option('--lang', '-l', help='Language, can be python/R.',
              default='')
def main(script, json, out, lang):
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


if __name__ == "__main__":
    main()
