################################################################################
# Configuration
################################################################################

RUN_LABEL					?=microwave-heating-pad-cherry
OUT_DIR						?=.out/niche-research/$(RUN_LABEL)
export AMZ_DEBUG			?=0

MAX_KEYWORDS                =100
MAX_ASINS					=1000

# Debug configuration
ifeq ($(AMZ_DEBUG),1)
	$(info ************  DEBUG VERSION ************)
	MAX_ASINS				=10
	MAX_KEYWORDS            =10
endif

################################################################################
# Target
################################################################################

all: $(OUT_DIR)/pipeline.done

clean:
		rm -rf $(OUT_DIR)

rebuild: clean $(OUT_DIR)/pipeline.done

$(OUT_DIR)/pipeline.done: \
		$(OUT_DIR)/asins.crawled
		
################################################################################
## STEPS
################################################################################

$(OUT_DIR)/search.done:    niche-keywords.txt
	set -e
	mkdir -p $(OUT_DIR)
	
	OUTPUT_FILE_NO_EXT=$(abspath $(basename $@)) \
		MAX_KEYWORDS=$(MAX_KEYWORDS) \
		KEYWORDS_FILE=$(realpath $<) \
			bash $(AMZ_SCRAPY_DIR)/launchers/local-amz-keywords.sh
	touch $@

$(OUT_DIR)/asins.txt: $(OUT_DIR)/search.done
	set -e
	cat $(basename $<).json | perl -ne 'print "$$2\n" while /\"(:?asin)\":\s\"([^\"]+)\"/g' | sort | uniq > $@

$(OUT_DIR)/asins.crawled: $(OUT_DIR)/asins.txt
	set -e
	mkdir -p $(OUT_DIR)
	
	OUTPUT_FILE_NO_EXT=$(abspath $(basename $@)) \
		AMZ_DP_PARSER_FULL_REVIEWS=1 \
		MAX_ASINS=$(MAX_ASINS) \
		ASINS_FILE=$(realpath $<) \
			bash $(AMZ_SCRAPY_DIR)/launchers/local-amz-dp.sh
	touch $@