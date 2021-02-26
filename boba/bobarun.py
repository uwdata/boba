import subprocess
import pandas as pd
import os
import json
import multiprocessing as mp
from subprocess import PIPE
from .lang import Lang
from .wrangler import *


class BobaRun:
    def __init__(self, folder, jobs=1):
        # path
        self.folder = folder

        # initialize process pool
        if jobs == 0:
            jobs = mp.cpu_count()
        self.jobs = jobs
        self.pool = mp.Pool(jobs)

        # read summary
        data = pd.read_csv(self.folder + '/summary.csv')
        self.size = data.shape[0]

        # language
        fn = data['Filename'].to_list()[0]
        try:
            with open(self.folder + '/lang.json', 'r') as f:
                self.lang = Lang(fn, supported_langs=json.load(f))
        except IOError:
            self.lang = Lang(fn)


    def run_multiverse(self, universes=[], batch_size=0):
        """
        Run the multiverse.
        
        Parameters:
         - universes: a list of universe filenames to run
         - batch size: the number of universes a processor will run in a row
        """
        # by default, run all universes
        if not len(universes):
            universes = [get_universe_script(i + 1, self.lang.get_ext()) \
                for i in range(self.size)]

        # before execute
        self.run_commands_in_folder('pre_exe.sh')

        # initialize the log folder and log file
        p_log = os.path.join(self.folder, DIR_LOG)
        if os.path.exists(p_log):
            shutil.rmtree(p_log)
        os.makedirs(p_log)

        with open(os.path.join(p_log, 'logs.csv'), 'w') as log:
            log.write('uid,exit_code\n')

        # callback that is run for each retrieved result.
        def check_result(r):
            # write the results to our logs
            with open(os.path.join(p_log, 'logs.csv'), 'a') as f_log:
                for res in r:
                    f_log.write(f'{res[0]},{res[1]}\n')

        # run each batch of universes as a separate task
        if batch_size == 0:
            batch_size = min(int(len(universes)**0.5),
                int(len(universes) / self.jobs) + 1)

        while universes:
            batch = []
            while universes and len(batch) < batch_size:
                batch.append(universes.pop(0))

            self.pool.apply_async(run_batch_of_universes,
                args=(self.folder, batch, self.lang.supported_langs),
                callback=check_result)

        # collect all the results
        self.pool.close()
        self.pool.join()

        # after execute
        self.run_commands_in_folder('post_exe.sh')


    def stop(self):
        """ Stop all outstanding work in the pool """
        print('Terminating')
        self.pool.terminate()
        self.pool.join()


    def run_from_cli(self, run_all=True, num=1, thru=-1, batch_size=0):
        """ Entry point of boba run CLI """
        # get the names of all the universes we want to run
        universes = []
        extension = self.lang.get_ext()
        if run_all:
            universes = [get_universe_script(i + 1, extension) \
                for i in range(self.size)]
        else:
            if thru == -1:
                thru = num
            for i in range(num, thru + 1):
                universe = get_universe_script(i, extension)
                universes.append(universe)

        # run
        self.run_multiverse(universes)


    def run_commands_in_folder(self, file_with_commands):
        """ Run command """
        cwd = os.getcwd()
        os.chdir(self.folder)
        with open(file_with_commands) as f:
            for line in f.readlines():
                os.system(line)
        os.chdir(cwd)



# these two functions can't be in the class because multiprocess
# does not know how to properly serialize functions in classes
def run_batch_of_universes(folder, universes, supported_langs):
    """ Run a batch of universes """
    batch = []
    for universe in universes:
        batch.append(run_universe(folder, universe, supported_langs))

    return batch


def run_universe(folder, script, supported_langs):
    """ Run one universe """
    cmds = Lang(script, supported_langs=supported_langs).get_cmd()

    universe_id = get_universe_id_from_script(script)
    universe_name_fmt = '[' + get_universe_name(universe_id) + ']'
    for cmd in cmds:
        out = subprocess.Popen(cmd, cwd=os.path.join(folder, DIR_SCRIPT),
                            stdout=PIPE, stderr=PIPE)

        log_dir = os.path.join(folder, DIR_LOG)
        with open(os.path.join(log_dir, get_universe_log(universe_id)), 'w') as log:
            while True:
                # blocks here until next line is availible.
                output = out.stdout.readline().decode('utf-8')
                if output == '' and out.poll() is not None:
                    break
                if output:
                    print(universe_name_fmt + " " + output, end='')
                    log.write(output)
                rc = out.poll()

        err = out.communicate()[1]
        err_decoded = err.decode('utf-8')
        if err_decoded is not '':
            with open(os.path.join(log_dir, get_universe_error_log(universe_id)), 'w') as err_log:
                err_log.write(err_decoded)
            
            print(universe_name_fmt + ' error:\n' + err_decoded, end='')
            break

    return universe_id, out.returncode
