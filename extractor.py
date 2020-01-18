import logging
import subprocess
import os

class Extractor():
    def __init__(self, project, clone=False, cleanup=False, explore=False, dirseparator=''):
        self.project = project
        self.clone = clone
        self.cleanup = cleanup
        self.explore = explore
        self.dirseparator = dirseparator
        basedir = os.getenv('REPOS_STORE', '~/tmp')
        self.directory = '"' + os.path.join(basedir, self.project['repo_name'].replace('/', dirseparator)) + '"'

    def run_cmd(self, args, env=None):
        return subprocess.check_output(' '.join(args), shell=True, env=env, executable='/bin/bash')

    def do_clone(self):
        repo_name = self.project['repo_name']

        logging.debug('Cloning %s', repo_name)

        repo_url = 'https://github.com/{0}.git'.format(repo_name)

        if self.cleanup:
            self.run_cmd(['rm -rf', self.directory, '&&', 'git clone', repo_url, self.directory])
        else:
            try:
                self.run_cmd(['git clone', repo_url, self.directory])
            except subprocess.CalledProcessError as error:
                # When not a "fatal: destination path '--REPO--' already exists and is not an empty directory."
                if error.returncode != 128:
                    raise error

    def run(self):
        if self.clone:
            self.do_clone()

        reponame = self.project['repo_name']
        library = self.project['library']
        from_commit = self.project.get('first_toggles_commit')

        logging.debug('Extracting %s', reponame)

        # TODO: not just python
        args = [self.directory, '"**/*.{py,html}"', '--history', library]

        if self.explore:
            args.append('--break')

        if from_commit:
            args.append('--from {0}'.format(from_commit))

        try:
            return self.run_cmd(['extractor'] + args + ['2>', '>(sed "s/^/({0}) /" 1>&2)'.format(reponame.replace('/', '\/'))])
        except subprocess.CalledProcessError as error:
            # Impossible to checkout. Skip
            # There seems to be a bug in git when you cannot move to another place because git checkout -- file
            # will allways show there are pending modifications. Looks related to autoctrl and lineendings.
            # https://stackoverflow.com/a/2016426/638425
            if error.returncode != 110:
                raise error

            # TODO: use no_toggles_skip
            return b''

