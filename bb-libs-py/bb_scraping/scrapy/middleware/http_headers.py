##############################################################################
# Copyright (c) BB Studio. All Rights Reserved.
##############################################################################

import os
import random

from bb_scraping.headers.user_agent import UserAgentProvider

ACCEPT_HEADER_CHOICES = [
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'text/html, application/xhtml+xml, image/jxr, */*',
    'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8'
]

# NOTE: Compression must be enabled in Accept-Encoding, so we consume less ingress traffic,
# which might be very pricy with certain proxy providers.
ACCEPT_ENCODING_HEADER_CHOICES = [
    'gzip, deflate', 'gzip, deflate, br', 'br, gzip, deflate',
    'gzip, deflate, sdch'
]

ACCEPT_LANGUAGE_HEADER_CHOICES = ['en-US, en', 'en-US,en;q=0.5', 'en-us']

REFERER_LANGUAGE_HEADER_CHOICES = [
    'https://www.facebook.com/',
    'https://www.bing.com/',
    'https://www.google.com/',
]

desktop_ua_provider = UserAgentProvider.load_desktop()
mobile_ua_provider = UserAgentProvider.load_mobile()


class RandomHeadersMiddleware(object):
    """
    Scrapy middleware to randomly choose a variation of
    HTTP headers for a typical desktop browser to send
    with a new request.

    NOTE it is not responsble for the User Agent header.
    """
    def __init__(self):
        self.http_host = os.environ.get('SCRAPY_HTTP_HOST')

    def process_request(self, request, spider):
        # http://stackoverflow.com/questions/37168688/how-can-i-change-order-of-http-headers-sent-by-scrapy
        request.headers['Accept'] = random.choice(ACCEPT_HEADER_CHOICES)

        request.headers['Accept-Encoding'] = random.choice(
            ACCEPT_ENCODING_HEADER_CHOICES)
        request.headers['Accept-Language'] = random.choice(
            ACCEPT_LANGUAGE_HEADER_CHOICES)

        request.headers['Referer'] = random.choice(
            REFERER_LANGUAGE_HEADER_CHOICES)

        if random.randint(0, 100) % 5 == 0:
            request.headers['Cache-Control'] = 'no-cache'

        if random.randint(0, 100) % 2 == 0:
            request.headers['Connection'] = 'keep-alive'

        if random.randint(0, 100) % 2 == 0:
            request.headers['Upgrade-Insecure-Requests'] = 1

        if random.randint(0, 100) % 7 == 0:
            request.headers['Dnt'] = '1'

        if random.randint(0, 100) % 11 == 0:
            request.headers['Alexatoolbar-Alx-Ns-Ph'] = 'AlexaToolbar/alx-4.0'

        if self.http_host and len(self.http_host) > 0:
            request.headers['Host'] = self.http_host


class RandomUserAgentMiddleware(object):
    """
    Scrapy middleware to set a random user agent string
    on each request.
    """
    def __init__(self):
        if os.environ.get('SCRAPY_DEVICE_TYPE') == 'mobile':
            self.user_agent_provider = mobile_ua_provider
        else:
            self.user_agent_provider = desktop_ua_provider

    def process_request(self, request, spider):
        user_agent = self.user_agent_provider.next()

        # NOTE if we use request.headers.setdefault() (as we did before) and
        # the default headers were already set by the scrapy's middlware - the
        # new user agent string won't be used
        request.headers['User-Agent'] = user_agent
