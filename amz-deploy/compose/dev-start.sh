#!/bin/sh

# Sample usage:
# ./docker-compose.local.sh up
# ./docker-compose.local.sh exec airflow bash
# ./docker-compose.local.sh down

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

AMZ_CODE_DIR=$AMZ_CODE_DIR \
AMZ_SECRETS_DIR=$AMZ_SECRETS_DIR \
    docker-compose \
        --project-directory "$AMZ_CODE_DIR" \
        -f "${SCRIPT_DIR}/base.yml" \
        -f "${SCRIPT_DIR}/dev-env.yml" \
        $@
