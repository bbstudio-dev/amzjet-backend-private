#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $SCRIPT_DIR/_init-local-run.sh

# Main job
#

rm -f $OUTPUT_FILE_NO_EXT.jsonlines
SCRAPY_PROJECT=amz_local_search_web \
SCRAPY_DEVICE_TYPE='mobile' \
	scrapy crawl AmzLocalSearchWeb \
		-a query=biotin \
        -a max_pages=9 \
		-a us_states_csv=CA,FL \
		-a num_samples=1 \
		-a tags_csv=device \
		\
		-s JOBDIR=$JOB_DIR \
		-t jsonlines \
		-o $OUTPUT_FILE_NO_EXT.jsonlines