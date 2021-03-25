##############################################################################
# Copyright (c) BB Studio. All Rights Reserved.
##############################################################################

from scrapy.spiders import Spider


class AmzBaseSpider(Spider):
    """
    Base class for spiders targeting Amazon.com
    """

    def __init__(self):
        pass

    def check_for_anti_robot_response(self, response):
        """ Called by the middleware to detect a blocked request """

        if response.text:
            if 'Enter the characters you see below' in response.text or \
                    'To discuss automated access to Amazon' in response.text:
                return {
                    'detected': True,
                    'retriable': True,
                    'allow_proxy_blocking': False
                }
