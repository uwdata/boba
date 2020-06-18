# -*- coding: utf-8 -*-

"""Console script."""
import click
import os
import subprocess
from .parser import Parser
from .output.csvmerger import CSVMerger
import multiprocessing as mp
import pandas as pd
from shutil import copyfile


@click.command()
@click.option('--script', '-s', help='Path to template script',
              default='./template.py', show_default=True)
@click.option('--out', help='Output directory',
              default='.', show_default=True)
@click.option('--lang', help='Language, can be python/R [default: inferred from file extension]',
              default='')
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

def run_universe(args):
    if(args[1].split('.')[1] == "py"):
        subprocess.run(["python", "-W", "ignore", args[1]], cwd=args[0] + "/code/")
    else:
        subprocess.run(["Rscript", args[1]], cwd=args[0] + "/code/")

@click.command()
@click.argument('num', nargs=1, default=-1)
@click.option('--all', '-a', 'run_all', is_flag=True,
              help='Execute all universes')
@click.option('--thru', default=-1, help='Run until this universe number')
@click.option('--proc', default=mp.cpu_count(), help='number of universes that can be running at a time')
@click.option('--dir', 'folder', help='Multiverse directory',
              default='./multiverse', show_default=True)
def run(folder, run_all, num, thru, proc):
    """ Execute the generated universe scripts.

    Run all universes: boba run --all

    Run a single universe, for example universe_1: boba run 1

    Run a range of universes for example 1 through 5: boba run 1 --thru 5
    """
    
    check_path(folder)
    # copy all the files in the current directory to the code directory
    # (in case there are data files we need)
    parent = os.path.abspath(os.path.join(folder, os.pardir)) + "/"
    
    files = [f for f in os.listdir(parent) if os.path.isfile(os.path.join(parent, f))]
    for f in files:
        copyfile(parent + f, folder + "/code/" + os.path.basename(f))

    # get the names of all the universes we want to run
    universes = []
    data = pd.read_csv(folder + "/summary.csv")
    vals = data['Filename'].values
    file_extension = vals[0].split('.')[1]
    if run_all:
        for universe in vals:
            universes.append([folder, universe])
    else:
        if thru == -1:
            thru = num

        for i in range(num, thru + 1):
            universe = "universe_" + str(i) + "." + file_extension
            universes.append([folder, universe])

    # run all of the universes
    # the number of universes we can run at a time is equal to proc
    pool = mp.Pool(proc)
    pool.map(run_universe, universes)


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
