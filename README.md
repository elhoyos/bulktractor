# bulktractor

Extract toggles from multiple repositories given in a csv and store the results in a directory

# Installation

Install the dependencies:

```bash
$ pip install -r requirements.txt
```

Make sure the `extractor` command is available in your `PATH`. If not install it.

```bash
$ extractor --help
```

Now, create a projects table in PostgreSQL database to keep track of the toggles extraction status:

```bash
$ createdb toggles
$ psql toggles -f projects.sql
```

And modify `config.py` to connect to your database.

# Usage

The help is a good staring point:

```bash
$ python bulktractor.py --help
```

Asuming the libraries in your `repositories.csv` file match the ones supported by `extractor-python`, you can extract all the toggles like this:

```bash
$ PYTHON_PATH=`pyenv which python` SCRIPT_PATH="~/extractor-python" REPOS_STORE="~/__REPOS_STORE" python bulktractor.py repositories.csv ./toggles
```

Notice the only environment variable required by bulktractor is `REPOS_STORE`. The rest are necessary for `extractor` or its specific language extractors.

## Bulktractor in parallel

You can take advantage of multiple CPUs and fast disks using GNU parallel to run various bulktractor instances at the same time. Here's an example that runs three bulktractor instances via `extract.sh` and sends their results to `./logs`:

```bash
$ psql toggles -t -A -c"SELECT repo_name FROM projects WHERE has_toggles is true" | \
    REPOS_STORE=~/repositories \
    parallel -j3 --results ./logs ./extract.sh
```

Here's another example running two instances in parallel and using a 4GiB RAM disk in OS X:

```bash
$ diskutil erasevolume HFS+ 'ReposDisk' `hdiutil attach -nomount ram://8388608`
$ cp ~/repositories/repo_A ~/repositories/repo_B /Volumes/ReposDisk
$ echo -e "repo_A\nrepo_B" | parallel -j2 --results ./logs ./extract.sh
```

# Useful scripts

### Reset repo HEAD to last commit

Running bulktractor with `DEBUG=toggles-diff*` and storing stderr has its advantages for reproducibility purposes. This could serve useful if you have recent versions of the repositories and want to set them up to reproduce the results here presented.

```bash
# last processed commit per repository
ls -b logs/1 | xargs -I{} sh -c 'tac "$PWD/logs/1/{}/stderr" | grep -m1 "toggles-diff "' | awk '{repo = $1 ; gsub(/\(|\)/, "", repo) ; print repo, $4}'

# last commit and repo
ls -b logs/1 | xargs -I{} sh -c 'tac "$PWD/logs/1/{}/stderr" | grep -m1 "toggles-diff " | awk '"'"'{print $4, "{}"}'"'"'' | xargs -n2 sh -c '$0 ---- "$1"'

# reset repo HEAD to last commit
ls -b logs/1 | xargs -I% sh -c 'tac "$PWD/logs/1/%/stderr" | grep -m1 "toggles-diff " | xargs echo "%$1"' | awk '{repodir = $1; gsub(/\\/, "_", repodir) ; print repodir, $5}' | xargs -n2 sh -c 'cd ~/_repositories/$0; pwd ; git reset --hard $1'
```

### Set commit to first toggle

If you ran bulktractor with `DEBUG=toggles-diff*` and you have those logs available, you can use the following command to generate sql update queries with the first commit where toggles were found for all the projects:

```bash
ls -b logs/1/*/stderr | xargs -I{} awk '{if ($3 == "toggles-diff") { repo = $1 ; gsub(/\(|\)/, "", repo) ; commit = $4; } if ($6 == "ADDED") exit} END {print "UPDATE projects SET first_toggles_commit = '\''"commit"'\'' WHERE repo_name = '\''"repo"'\''"}' {} > update.sql
```
