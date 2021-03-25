##############################################################################
# Copyright (c) BB Studio. All Rights Reserved.
##############################################################################

import os

from scrapy.item import Item, Field


class GenericItem(Item):
    key = Field()

    request_url = Field()

    response_url = Field()

    crawl_date = Field()

    payload_type = Field()

    payload = Field()

    size = Field()

    page_index = Field()

    page_size = Field()

    trace = Field()

    def __repr__(self):
        # Check if we want the full item to be logged.
        log_item_flag = os.environ.get('SCRAPY_LOG_ITEMS')
        if log_item_flag is None or int(log_item_flag):
            return super(GenericItem, self).__repr__()
        else:
            return repr({
                'key': self['key'],
                'payload_size': len(self.get('payload') or {})
            })
