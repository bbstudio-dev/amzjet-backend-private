from bb_scraping.scrapy.middleware.proxy import RandomProxyMiddlewareBase
from amz_glue.phantom import proxy_provider


class RandomProxyMiddleware(RandomProxyMiddlewareBase):
    def __init__(self, options, stats):
        super(RandomProxyMiddleware, self).__init__(options, stats)

    def _load_proxies(self):
        return proxy_provider.get_proxies_for()
