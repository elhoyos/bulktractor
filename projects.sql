CREATE TABLE projects (
  repo_name TEXT UNIQUE,
  library TEXT,
  library_language TEXT,
  number_of_commits INT,
  has_toggles BOOLEAN,
  processed BOOLEAN,
  processing BOOLEAN DEFAULT false,
  first_toggles_commit TEXT DEFAULT NULL
);
