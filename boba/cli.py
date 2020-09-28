# -*- coding: utf-8 -*-

"""Console script."""
import json
import click
import shutil
from .parser import Parser
from .output.csvmerger import CSVMerger
import multiprocessing as mp
import pandas as pd
from .bobarun import *
from .wrangler import get_universe_script, DIR_LOG


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

    # get the names of all the universes we want to run
    universes = []
    data = pd.read_csv(folder + '/summary.csv')
    vals = data['Filename'].to_list()
    
    try:
        with open(folder + '/lang.json', 'r') as f:
            lang = Lang(vals[0], supported_langs=json.load(f))
    except IOError:
        lang = Lang(vals[0])

        
    extension = lang.get_ext()
    if run_all:
        universes = vals
    else:
        if thru == -1:
            thru = num
        if num < 1:
            print_help()
        if thru < num:
            print_help('The thru parameter cannot be less than the num parameter.')
        if num >= len(vals) or thru >= len(vals):
            print_help('There are only ' + str(len(vals)) + ' universes.')

        for i in range(num, thru + 1):
            universe = get_universe_script(i, extension)
            print(universe)
            universes.append(universe)

    run_commands_in_folder(folder, 'pre_exe.sh')

    if jobs == 0:
        jobs = mp.cpu_count()

    if batch_size == 0:
        batch_size = min(int(len(universes)**0.5), int(len(universes)/jobs) + 1)

    pool = mp.Pool(jobs)

    results = []

    p_log = os.path.join(folder, DIR_LOG)
    if os.path.exists(p_log):
        shutil.rmtree(p_log)
    os.makedirs(p_log)

    with open(os.path.join(p_log, 'logs.csv'), 'w') as log:
        log.write('universe,exit_code\n')

    # callback that is run for each retrieved result.
    def check_result(r):
        results.extend(r)
        # write the results to our logs
        with open(os.path.join(p_log, 'logs.csv'), 'a') as f_log:
            for res in r:
                f_log.write(res[0] + ',' + str(res[1]) + '\n')


    # run each batch of universes as a separate task
    while universes:
        batch = []
        while universes and len(batch) < batch_size:
            batch.append(universes.pop(0))

        pool.apply_async(run_batch_of_universes, args=(folder, batch, lang.supported_langs), callback=check_result)

    # collect all the results
    pool.close()
    pool.join()

    run_commands_in_folder(folder, 'post_exe.sh')


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
