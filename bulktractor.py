import argparse
import os
import logging
import threading
import sys
from extractor import Extractor
from state import State

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
no_toggles_json = '{"Declaration":{},"Router":{},"Point":{}}'
no_toggles_skip = ''

OWNER_REPO_SEPARATOR = '__'

def extract_toggles(args, kwargs):
    dryrun = kwargs.pop('dryrun', None)
    extractor = Extractor(*args, **kwargs)
    if dryrun == True:
        extractor.do_clone()
        return b''

    return extractor.run()

if __name__ == '__main__':
    # TODO: help='Environment variables are passed to extractor commands. Use REPOS_STORE'
    parser = argparse.ArgumentParser('Extract the toggles from a list of projects and save results into a specified directory')
    parser.add_argument('projects_csv', help='A csv containing the projects to extract the toggles from')
    parser.add_argument('output_dir', help='The output directory where resulting files will be placed')
    parser.add_argument('repositories', nargs='*', help='Extract from only these repository names')
    parser.add_argument('--clone', action='store_true', help='Attempt to clone the repositories')
    parser.add_argument('--cleanup', action='store_true', help='Ignore the cached repositories')
    parser.add_argument('--explore', action='store_true', help='Check if the repositories have toggles and update their state')
    parser.add_argument('--dryrun', action='store_true', help='Load and clone repositories but do not extract toggles')

    args = parser.parse_args()
    csv_filename = args.projects_csv
    outdir = args.output_dir
    repositories = args.repositories
    clone = args.clone
    cleanup = args.cleanup
    explore = args.explore
    dryrun = args.dryrun

    state = State(csv_filename, only=repositories)
    state.store_projects()

    kwargs = {
        'clone': clone,
        'cleanup': cleanup,
        'explore': explore,
        'dirseparator': OWNER_REPO_SEPARATOR,
        'dryrun': dryrun,
    }
    for project in state.projects():
        toggles = extract_toggles([project], kwargs)
        filename = project['repo_name'].replace('/', OWNER_REPO_SEPARATOR) + '.json'
        with open(os.path.join(outdir, filename), 'wb') as file:
            file.write(toggles)

        decoded_toggles = toggles.decode('utf-8')
        has_toggles = decoded_toggles != no_toggles_skip and decoded_toggles != no_toggles_json
        state.done(project, has_toggles)
