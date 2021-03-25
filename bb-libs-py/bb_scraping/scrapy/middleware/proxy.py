##############################################################################
# Copyright (c) BB Studio. All Rights Reserved.
##############################################################################

import base64
import logging
import random


##############################################################################
# Scrapy middleware.
##############################################################################

class RandomProxyMiddlewareBase(object):
    """
    Scrapy middleware choosing a random proxy for each new request.
    """

    def __init__(self, options, stats):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.stats = stats

        # Share the same configuration key as the RetryMiddleware
        # https://github.com/scrapy/scrapy/blob/master/scrapy/downloadermiddlewares/retry.py
        self.max_retry_times = options.getint('RETRY_TIMES')
        self.priority_adjust = options.getint('RETRY_PRIORITY_ADJUST')

        self.choose_proxy_randomly = False
        self.next_proxy_idx = -1

        self.logger.info('Loading proxies...')
        self.proxies = list(self._load_proxies())
        self.initial_proxy_count = len(self.proxies)
        random.shuffle(self.proxies)
        self.logger.info('Loaded %d proxies.' % len(self.proxies))

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            crawler.settings,
            crawler.stats
        )

    def process_request(self, request, spider):
        self._set_proxy_on_request(request)

    def process_response(self, request, response, spider):
        if request.meta.get('dont_retry', False):
            return response

        check_for_anti_robot_response = getattr(
            spider, "check_for_anti_robot_response", None)
        if callable(check_for_anti_robot_response):
            anti_robot_test = check_for_anti_robot_response(response) or {}
            if anti_robot_test.get('detected'):
                return self._handle_anti_robot_response(anti_robot_test,
                                                        request, response,
                                                        spider) or response

        return response

    def _set_proxy_on_request(self, request):
        if len(self.proxies) == 0:
            return

        if self.choose_proxy_randomly:
            p = random.choice(self.proxies)
        else:
            self.next_proxy_idx = ((self.next_proxy_idx + 1) % len(self.proxies))
            p = self.proxies[self.next_proxy_idx]

        # http://stackoverflow.com/a/29716179/832700
        request.meta['proxy'] = 'http://%s:%s' % (p.host, p.port)

        # The 'download_slot' determines the key used to throttle requests. In this case we want
        # to throttle based on the proxy information (host, port). Some proxies may accept
        # parameters via credentials.
        # http://stackoverflow.com/a/26224172/832700
        # https://github.com/scrapy/scrapy/blob/e748ca50ca3e83ac703e02538a27236fedd53a7d/scrapy/contrib/throttle.py#L55
        # https://github.com/scrapy/scrapy/blob/ebef6d7c6dd8922210db8a4a44f48fe27ee0cd16/scrapy/core/downloader/__init__.pyrot
        # https://groups.google.com/forum/#!msg/scrapy-users/xDC-q-5FUrQ/seloXlBQAacJ
        request.meta['download_slot'] = p.id

        if p.user:
            encoded_user_pass = base64.b64encode(
                (p.user + ':' + p.password).encode('utf-8'))
            request.headers['Proxy-Authorization'] = 'Basic ' + \
                encoded_user_pass.decode('utf-8')

    def _handle_anti_robot_response(self, anti_robot_check,
                                    request, response, spider):
        if not anti_robot_check.get('detected'):
            return

        proxy = request.meta.get('proxy')
        self.logger.warn("Anti-robot response detected: %s (proxy: %s)" % (request, proxy))
        self.stats.inc_value('anti_robot/blocked_requests', spider=spider)

        if anti_robot_check.get('allow_proxy_blocking'):
            # SLOW: exclude failed proxy from the list
            self.proxies = [
                p for p in self.proxies if p.host != proxy]
            self.logger.warn(
                'Blocked %s proxy due to anti-robot response. Have %d left.'
                % (proxy, len(self.proxies)))
            self.stats.set_value(
                'anti_robot/blocked_proxies',
                self.initial_proxy_count - len(self.proxies), spider=spider)

        if anti_robot_check.get('retriable'):
            return self._retry(request, spider)

    # Based on
    # https://github.com/scrapy/scrapy/blob/master/scrapy/downloadermiddlewares/retry.py
    def _retry(self, request, spider):
        retries = request.meta.get('retry_times', 0) + 1

        reason = 'Anti-robot protection'

        if retries <= self.max_retry_times:
            self.logger.debug(
                "Retrying %(request)s (failed %(retries)d times): %(reason)s",
                {
                    'request': request,
                    'retries': retries,
                    'reason': reason
                },
                extra={'spider': spider})
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust

            self.stats.inc_value('anti_robot/retried_requests', spider=spider)

            # Change proxy
            self._set_proxy_on_request(retryreq)

            return retryreq
        else:
            self.logger.warn(
                "Gave up retrying %(request)s (failed %(retries)d times): "
                "%(reason)s",
                {
                    'request': request,
                    'retries': retries,
                    'reason': reason
                },
                extra={'spider': spider})
            self.stats.inc_value('anti_robot/gave_up_requests', spider=spider)

    def _load_proxies(self):
        raise NotImplementedError()
