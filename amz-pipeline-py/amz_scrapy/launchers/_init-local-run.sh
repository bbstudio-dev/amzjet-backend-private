#!/bin/bash
set -e

command -v scrapy >/dev/null 2>&1 || { echo >&2 "Scrapy not installed. Make sure to run this script from a preconfigured environment like VirtualEnv. Aborting."; exit 1; }

# Determine script's location
#

# Get the script's directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

SCRIPT_NAME="$( basename "$0" )" 
SCRIPT_NAME="${SCRIPT_NAME%.*}"

SCRAPY_PROJECT_DIR=$SCRIPT_DIR/..

export SCRIPT_DIR
export SCRAPY_PROJECT_DIR

# Set proxy database for Scrapy's middleware
#

export PROXY_DB_URI=${PROXY_DB_URI:-$AMZ_MONGO_URI}
export PROXY_ROLE=${PROXY_ROLE:-generic}

# Determine script's location
#

OUTPUT_FILE_NO_EXT=${OUTPUT_FILE_NO_EXT:-$AMZ_LOCAL_STAGE_DIR/scrapy-launchers/$SCRIPT_NAME}

WORK_DIR=$OUTPUT_FILE_NO_EXT

JOB_ID=$JOB_ID
JOB_DIR=$WORK_DIR/crawler/$JOB_ID

# Restart crawling from scratch by erasing the current job directory
#

rm -rf $JOB_DIR
mkdir -p $WORK_DIR

# Change current directory
#

cd $SCRAPY_PROJECT_DIR