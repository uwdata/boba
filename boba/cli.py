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


def run_batch_of_universes(folder, universes):
    batch = []
    for universe in universes:
        batch.append(run_universe(folder, universe))

    return batch

def run_universe(folder, script):
    out = None
    # choose python or R based on file extension of provided universe
    if(script.split('.')[1] == "py"):
        out = subprocess.Popen(["python", "-W", "ignore", script], cwd=folder + "/code/")
    else:
        out = subprocess.Popen(["Rscript", script], cwd=folder + "/code/")
    # it's ok to block here because this function will be running as a seperate process
    out.communicate()

    return (script.split('.')[0], out.returncode)


def run_commands_in_folder(folder, file_with_commands):
    cwd = os.getcwd()
    os.chdir(folder)
    with open(file_with_commands) as f:
        for line in f.readlines():
            os.system(line)
    os.chdir(cwd)

@click.command()
@click.argument('num', nargs=1, default=-1)
@click.option('--all', '-a', 'run_all', is_flag=True,
              help='Execute all universes')
@click.option('--thru', default=-1, help='Run until this universe number')
@click.option('--jobs', default=1, help='number of universes that can be running at a time. Set to 0 to make this the number of cores on the computer.')
@click.option('--batch_size', default=0, help='the approximate number of universes a processor will run in a row. Has no effect if the number of jobs is 1.')
@click.option('--dir', 'folder', help='Multiverse directory',
              default='./multiverse', show_default=True)
def run(folder, run_all, num, thru, jobs, batch_size):
    """ Execute the generated universe scripts.

    Run all universes: boba run --all

    Run a single universe, for example universe_1: boba run 1

    Run a range of universes for example 1 through 5: boba run 1 --thru 5
    """
    
    check_path(folder)

    # get the names of all the universes we want to run
    universes = []
    data = pd.read_csv(folder + "/summary.csv")
    vals = data['Filename'].values
    file_extension = vals[0].split('.')[1]
    if run_all:
        for universe in vals:
            universes.append(universe)
    else:
        if thru == -1:
            thru = num

        for i in range(num, thru + 1):
            universe = "universe_" + str(i) + "." + file_extension
            universes.append(universe)

    run_commands_in_folder(folder, "pre_exe")

    if jobs == 0:
        jobs = mp.cpu_count()

    if batch_size == 0:
        batch_size = min(int(len(universes)**(0.5)), int(len(universes)/mp.cpu_count()) + 1)

    pool = mp.Pool(jobs)

    results = []

    # callback that is run for each retrieved result.
    def check_result(r):
        results.extend(r)
        for res in r:
            if res[1] != 0:
                pool.terminate() # end computation if one of the processes broke
    
    # run each batch of universes as a seperate task
    while universes:
        batch = []
        while universes and len(batch) < batch_size:
            batch.append(universes.pop(0))

        pool.apply_async(run_batch_of_universes, args=(folder, batch), callback=check_result)
    
    # collect all the results
    pool.close()
    pool.join()

    # write the results to our logs
    if not os.path.exists(folder + "/boba_logs/"):
        os.makedirs(folder + "/boba_logs/")

    with open(folder + "/boba_logs/logs", 'w') as log:
        for result in results:
            log.write(result[0] + " " + str(result[1]) + "\n")
            
    run_commands_in_folder(folder, "post_exe")


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
