# -*- coding: utf-8 -*-

"""Console script."""
import click
import shutil
import os
import pandas as pd
from .parser import Parser
from .output.csvmerger import CSVMerger
from .bobarun import BobaRun


@click.command()
@click.option('--script', '-s', help='Path to template script',
              default='./template.py', show_default=True)
@click.option('--out', help='Output directory',
              default='.', show_default=True)
@click.option('--lang', help='Language, can be python/R [default: inferred from file extension]',
              default=None)
def compile(script, out, lang):
    """Generate multiverse analysis from specifications."""

    check_path(script)

    click.echo('Creating multiverse from {}'.format(script))
    ps = Parser(script, out, lang)
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
@click.option('--jobs', default=1, help='The number of universes that can be running at a time.')
@click.option('--batch_size', default=0, help='The approximate number of universes a processor will run in a row.')
@click.option('--dir', 'folder', help='Multiverse directory',
              default='./multiverse', show_default=True)
def run(folder, run_all, num, thru, jobs, batch_size):
    """ Execute the generated universe scripts.

    Run all universes: boba run --all

    Run a single universe, for example universe_1: boba run 1

    Run a range of universes for example 1 through 5: boba run 1 --thru 5
    """

    check_path(folder)

    df = pd.read_csv(folder + '/summary.csv')
    num_universes = df.shape[0]

    if not run_all:
        if thru == -1:
            thru = num
        if num < 1:
            print_help()
        if thru < num:
            print_help('The thru parameter cannot be less than the num parameter.')
        if num > num_universes or thru > num_universes:
            print_help(f'There are only {num_universes} universes.')

    br = BobaRun(folder, jobs, batch_size)
    br.run_from_cli(run_all, num, thru)


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
