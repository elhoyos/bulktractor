#!/bin/bash

DEBUG=* \
PYTHON_PATH=`pyenv which python` \
SCRIPT_PATH=~/Projects/extractor-python \
REPOS_STORE="${REPOS_STORE:-/Volumes/ReposDisk}" \
    python bulktractor.py \
        ../analysis/waffle_repositories.csv \
        toggles \
        "$@"
