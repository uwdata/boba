# -*- coding: utf-8 -*-

"""Console script."""
import click
import os
import subprocess
from .parser import Parser
from .output.csvmerger import CSVMerger


@click.command()
@click.option('--script', '-s', help='Path to template script',
              default='./template.py', show_default=True)
@click.option('--json', '-j', help='Path to JSON spec',
              default='./spec.json', show_default=True)
@click.option('--out', help='Output directory',
              default='.', show_default=True)
@click.option('--lang', help='Language, can be python/R [default: inferred from file extension]',
              default='')
def compile(script, json, out, lang):
    """Generate multiverse analysis from specifications."""

    check_path(script)
    check_path(json)

    click.echo('Creating multiverse from {} and {}'.format(script, json))
    ps = Parser(script, json, out, lang)
    ps.main()

    ex = """To execute the multiverse, run the following commands:
    boba run --all
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


@click.command()
@click.argument('num', nargs=1, default=-1)
@click.option('--all', '-a', 'run_all', is_flag=True,
              help='Execute all universes')
@click.option('--thru', default=-1, help='Run until this universe number')
@click.option('--dir', 'folder', help='Multiverse directory',
              default='./multiverse', show_default=True)
def run(folder, run_all, num, thru):
    """ Execute the generated universe scripts.

    Run all universes: boba run --all

    Run a single universe, for example universe_1: boba run 1

    Run a range of universes for example 1 through 5: boba run 1 --thru 5
    """

    check_path(folder)

    if num < 0 and not run_all:
        print_help('Error: Missing argument "NUM".')

    cmd = ['sh', 'execute.sh']
    if not run_all:
        cmd.append(str(num))
        if thru > 0:
            cmd.append(str(thru))

    subprocess.run(cmd, cwd=folder)


@click.command()
@click.argument('pattern', nargs=1)
@click.option('--base', '-b', default='./multiverse/results',
              show_default=True, help='Folder containing the universe outputs')
@click.option('--out', default='./multiverse/merged.csv',
              show_default=True, help='Name of the merged file')
@click.option('--delimiter', default=',', show_default=True,
              help='CSV delimiter')
def merge(pattern, base, out, delimiter):
    """
    Merge CSV outputs from individual universes into one file.

    Required argument:
    the filename pattern of individual outputs where the universe id is
    replaced by {}, for example output_{}.csv
    """

    check_path(base)
    CSVMerger(pattern, base, out, delimiter).main()


@click.group()
@click.version_option()
def main():
    pass


main.add_command(compile)
main.add_command(run)
main.add_command(merge)

if __name__ == "__main__":
    main()
