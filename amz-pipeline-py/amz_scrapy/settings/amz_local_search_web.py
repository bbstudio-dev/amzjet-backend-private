##############################################################################
# Scrapy config for accessing web pages on Amazon.com
#
# This config has been used to sucessfully scrape:
# - Amazon bestseller pages. Last test: August 1, 2019.
#
# NOTE: Product details pages seems to have stricter bot protection, so
# access to those pages needs a different config.
#
# Copyright (c) BB Studio. All Rights Reserved.
##############################################################################

import os

script_dir = os.path.dirname(os.path.realpath(__file__))

BOT_NAME = 'crawler'

SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'

AUTOTHROTTLE_ENABLED = False
CONCURRENT_REQUESTS_PER_IP = 1
CONCURRENT_REQUESTS = 25
DOWNLOAD_DELAY = 5

DOWNLOAD_TIMEOUT = 20

COOKIES_ENABLED = False

DOWNLOADER_MIDDLEWARES = {
    'bb_scraping.scrapy.middleware.http_headers.RandomUserAgentMiddleware':
    400,
    'bb_scraping.scrapy.middleware.http_headers.RandomHeadersMiddleware': 600
}

FEED_EXPORTERS = {
    'jsonlines.gz': 'bb_scraping.scrapy.exporters.JsonLinesGzipItemExporter',
}
