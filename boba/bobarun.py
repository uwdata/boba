import subprocess
import pandas as pd
import os
import json
import multiprocessing as mp
from subprocess import PIPE
from .lang import Lang
from .wrangler import *


class BobaRun:
    def __init__(self, folder, jobs=1, batch_size=0):
        # attributes
        self.folder = folder
        self.dir_log = os.path.join(folder, DIR_LOG)
        self.file_log = os.path.join(self.dir_log, 'logs.csv')
        self.pool = None
        self.exit_code = []

        # read summary
        data = pd.read_csv(self.folder + '/summary.csv')
        self.size = data.shape[0]

        # multiprocessing attributes
        if jobs == 0:
            jobs = mp.cpu_count()
        if batch_size == 0:
            batch_size = min(int(self.size**0.5), int(self.size / jobs) + 1)
        self.jobs = jobs
        self.batch_size = batch_size

        # language
        fn = data['Filename'].to_list()[0]
        try:
            with open(self.folder + '/lang.json', 'r') as f:
                self.lang = Lang(fn, supported_langs=json.load(f))
        except IOError:
            self.lang = Lang(fn)


    def run_multiverse(self, universes=[], resume=False):
        """
        Run the multiverse.
        
        Parameters:
         - universes: a list of universe ids to run
         - resume: skip log initialization and pre-exe hook, but the caller must
           make sure that these steps are done properly before calling
        """
        # do not allow simultaneous runs
        if self.is_running():
            return

        # initialize process pool
        self.pool = mp.Pool(self.jobs)

        # by default, run all universes
        if not len(universes):
            universes = list(range(1, self.size + 1))

        if not resume:
            # before execute
            self.run_commands_in_folder('pre_exe.sh')

            # initialize the log folder and log file
            self.exit_code = []
            if os.path.exists(self.dir_log):
                shutil.rmtree(self.dir_log)
            os.makedirs(self.dir_log)

            with open(self.file_log, 'w') as log:
                log.write('uid,exit_code\n')

        # callback that is run for each retrieved result.
        # FIXME: if stopped, the last batch will not invoke the callback
        def check_result(r):
            self.exit_code += [[res[0], res[1]] for res in r]
            # write the results to our logs
            with open(self.file_log, 'a') as f_log:
                for res in r:
                    f_log.write(f'{res[0]},{res[1]}\n')

        # run each batch of universes as a separate task
        while len(universes):
            batch = []
            while len(universes) and len(batch) < self.batch_size:
                u = get_universe_script(universes.pop(0), self.lang.get_ext())
                batch.append(u)

            self.pool.apply_async(run_batch_of_universes,
                args=(self.folder, batch, self.lang.supported_langs),
                callback=check_result)

        # collect all the results
        self.pool.close()
        self.pool.join()

        # after execute
        self.run_commands_in_folder('post_exe.sh')
        self.pool = None


    def resume_multiverse(self, universes=[]):
        """
        Resume the multiverse, by skipping scripts that are already run in the
        universe list.
        """
        # if the log file is missing, run everything
        if not os.path.exists(self.file_log):
            return self.run_multiverse(universes)

        # default argument
        if not len(universes):
            universes = list(range(1, self.size + 1))

        # recover previous progress from log file
        df = pd.read_csv(self.file_log)
        self.exit_code = df.values.tolist()

        # skip scripts that are already run
        lookup = set(df['uid'].tolist())
        universes = [u for u in universes if u not in lookup]
        self.run_multiverse(universes, resume=True)


    def stop(self):
        """ Stop all outstanding work in the pool """
        if self.pool is not None:
            print('Terminating')
            # stop all workers
            # note that everything after pool.join() will still run
            self.pool.terminate()


    def is_running(self):
        """ Whether the multiverse is currently running """
        return self.pool is not None


    def run_from_cli(self, run_all=True, num=1, thru=-1):
        """ Entry point of boba run CLI """
        # get the id of all the universes we want to run
        thru = num if thru == -1 else thru
        start = 1 if run_all else num
        end = self.size if run_all else thru
        universes = list(range(start, end + 1))

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


    def run_after_execute(self):
        self.run_commands_in_folder('post_exe.sh')


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
