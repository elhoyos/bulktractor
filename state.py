import logging
import config
import psycopg2
import csv

class State():
    cursor = None
    conn = None

    def __init__(self, csv_filename, only=[]):
        self.csv_filename = csv_filename
        self.only = only
        self.init()
        self.__projects = {}

    def init(self):
        # Singleton the cursor to the db
        if not State.cursor:
            logging.debug('Connecting to database...')
            self.conn = psycopg2.connect("host= '{host}' dbname= '{dbname}' user='{username}' port={port}".format_map(config.db))
            logging.info('Connected to database')

            State.cursor = self.conn.cursor()

        self.cursor = State.cursor

    def add(self, project):
        self.__projects[project['repo_name']] = project

        try:
            self.cursor.execute(
                ' '.join([
                    'INSERT INTO projects',
                    '(repo_name, library, library_language, number_of_commits, first_toggles_commit)',
                    'VALUES',
                    '(%s, %s, %s, %s, %s)'
                ]),
                [
                    project['repo_name'],
                    project['library'],
                    project['library_language'],
                    project['number_of_commits'],
                    project.get('first_toggles_commit', None),
                ]
            )
        except psycopg2.IntegrityError:
            self.conn.rollback()
        else:
            self.conn.commit()

    def store_projects(self):
        only = self.only
        load_all = len(only) == 0
        with open(self.csv_filename, 'r') as file:
            reader = csv.DictReader(file)
            for project in reader:
                if load_all or project['repo_name'] in only:
                    self.add(project)

    def projects(self):
        while True:
            self.cursor.execute(' '.join([
                'UPDATE projects SET processing = true',
                'WHERE repo_name = (',
                '   SELECT repo_name',
                '   FROM projects',
                '   WHERE processing is not true and',
                '   processed is not true',
                '   {0}'.format(\
                        ''.join([
                            "and repo_name in ('",
                            "','".join([repo_name for repo_name in self.only]),
                            "')"
                        ]) if len(self.only) > 0 else ''\
                    ),
                '   ORDER BY number_of_commits ASC',
                '   LIMIT 1',
                '   FOR UPDATE',
                ')',
                'RETURNING repo_name'
            ]))
            results = self.cursor.fetchone()
            self.conn.commit()
            if results:
                project = results[0]
                if project in self.__projects:
                    yield self.__projects[project]
            else:
                break

    def done(self, project, has_toggles = False):
        self.cursor.execute("UPDATE projects set processed = true, processing = false, has_toggles = {0} where repo_name = '{1}';".format(has_toggles, project['repo_name']))
        self.conn.commit()