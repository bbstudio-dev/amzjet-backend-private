import base64
import datetime
import itertools
import logging
import os
import sys
import uuid

from scrapy.http.request import Request
from scrapy.http import HtmlResponse
from scrapy.selector import Selector

from six.moves.urllib.parse import quote
from amz_scrapy.items import GenericItem
from amz_scrapy.spiders.amazon.spider_base import AmzBaseSpider
from amz_scrapy.spiders.amazon.local_search.web_results_parser import parse_search_results  # noqa

_script_dir = os.path.dirname(os.path.realpath(__file__))
_resources_dir = os.path.join(_script_dir, 'resources')
_research_dir = os.path.join(_script_dir, 'research')


def parse_csv(csv):
    for s in csv.split(','):
        s = s.strip()
        if s:
            yield s


def parse_constants_csv(csv):
    for s in parse_csv(csv):
        yield s.upper()


class AmzLocalSearchWebSpider(AmzBaseSpider):
    name = 'AmzLocalSearchWeb'

    OXYLABS_USER = 'rzontracker'

    OXYLABS_PASSWORD = 'te85xcVZBx'

    def __init__(self,
                 query,
                 max_pages=3,
                 max_locations=sys.maxsize,
                 us_states_csv=None,
                 num_samples=1,
                 tags_csv=None,
                 tracking_id=None):
        self.log = logging.getLogger(self.__class__.__name__)

        self.query = query
        self.max_pages = int(max_pages)
        self.max_locations = int(max_locations)
        self.us_states = None if not us_states_csv else list(
            parse_constants_csv(us_states_csv))
        self.tags = None if not tags_csv else list(parse_csv(tags_csv))
        self.num_samples = int(num_samples)
        self.tracking_id = tracking_id

        # NOTE: Search results seem to have a lot of variability. Many factors
        # may contribute to that including randomly choosing different cities
        # within a state, looking as different search sessions to Amazon when
        # requesting search results/pages, triggering different algorithm
        # versions (weblabs), Amazon having regional replica of the index in
        # different state and etc.

        # Until we fix middleware to use the same headers per session, no
        # need to pretend sending requests from the same user.
        self.get_pages_in_parallel = True
        # Same as above.
        self.use_sticky_proxy_session = False

        # The default expected number of results for desktop is 60 - 12 = 48.
        self.min_expected_results_on_page_to_stop = 25

        self._load_locations_from_us_states()

    def _load_locations_from_us_states(self):
        self.state_short_to_full_map = {}
        self.locations = []

        with open(os.path.join(_resources_dir, 'us_states.csv')) as file:
            for line in file:
                line = line.strip()
                if line.startswith('#'):
                    continue
                parts = line.split(',')

                state_full = parts[0]
                state_abbrev = parts[1]
                self.state_short_to_full_map[state_abbrev] = state_full

        us_states_to_scrape = (self.us_states
                               or self.state_short_to_full_map.keys())
        for state in us_states_to_scrape:
            self.locations.append({'country': 'US', 'state': state})

    def _location_to_key(self, location):
        return '%s_%s' % (location['country'], location['state'])

    def start_requests(self):
        for sample_index in xrange(0, self.num_samples):
            for location in itertools.islice(self.locations, 0,
                                             self.max_locations):
                args = self._args(self.query, location, self.max_pages,
                                  self.tracking_id)

                if self.get_pages_in_parallel:
                    proxy_session_id = str(uuid.uuid4()).replace('-', '')
                    for page_num in xrange(1, self.max_pages + 1):
                        yield self._make_unordered_page_request(
                            args, page_num, proxy_session_id)
                else:
                    yield self._make_first_request(args)

    def _args(self, query, location, max_pages, tracking_id):
        obj = {
            'query': query,
            'location': location,
            'max_pages': max_pages,
            'tracking_id': tracking_id
        }
        return obj

    def _make_first_request(self, args):
        proxy_session_id = str(uuid.uuid4()).replace('-', '')
        return self._make_request(args,
                                  page_num=1,
                                  amazon_query_id=None,
                                  proxy_session_id=proxy_session_id,
                                  first_item_rank=1)

    def _maybe_make_next_request(self, last_request, parsed_data):
        # Query id seems to be just a timestamp like 1566027531.
        # I think we can fake it.
        amazon_query_id = parsed_data['meta']['internal']['query_id']

        normal_results_count = parsed_data['meta']['parser']['num_products']
        normal_results_count -= parsed_data['meta']['parser']['num_sponsored']

        last_meta = last_request.meta

        if normal_results_count == 0 or (
                normal_results_count <
                self.min_expected_results_on_page_to_stop):
            return None

        next_page_num = last_meta['search_page_num'] + 1
        if next_page_num > last_meta['args']['max_pages']:
            return None

        first_item_rank = last_meta['first_item_rank'] + normal_results_count
        return self._make_request(
            last_meta['args'],
            page_num=next_page_num,
            amazon_query_id=amazon_query_id,
            proxy_session_id=last_meta['proxy_session_id'],
            first_item_rank=first_item_rank)

    def _make_unordered_page_request(self,
                                     args,
                                     page_num,
                                     proxy_session_id,
                                     amazon_query_id=None):
        return self._make_request(args=args,
                                  page_num=page_num,
                                  amazon_query_id=amazon_query_id,
                                  proxy_session_id=proxy_session_id)

    def _make_request(self,
                      args,
                      page_num,
                      amazon_query_id,
                      proxy_session_id,
                      first_item_rank=None):
        search_url = 'https://www.amazon.com/s?k=%s' % quote(self.query)

        if page_num > 1:
            search_url += '&page=%d' % page_num

        # TODO: Do not pass qid until we fix the issue with random headers.
        # if amazon_query_id:
        #     search_url += '&qid=%s' % amazon_query_id

        # TODO: If we want to simulate the same user navigating through pages,
        # we need to set headers/ua only for the request to the first page.
        # Otherwise headers/ua are configured to change randomly for every
        # request.
        request = Request(search_url,
                          dont_filter=True,
                          meta={
                              'args': args,
                              'amazon_query_id': amazon_query_id,
                              'search_page_num': page_num,
                              'proxy_session_id': proxy_session_id,
                              'first_item_rank': first_item_rank
                          },
                          callback=self.parse_response,
                          errback=self.process_failure)

        # For subsequent results, make sure to reuse proxy.
        self._set_proxy_on_request(request)

        return request

    def parse_response(self, response):
        if self._test_anti_robot_response(response):
            return

        request = response.request

        query = response.request.meta['args']['query']
        location = response.request.meta['args']['location']

        item = GenericItem()
        item['key'] = query
        item['request_url'] = response.request.url
        item['crawl_date'] = datetime.datetime.utcnow().isoformat()

        item['payload_type'] = 'search-web-local'

        parsed_data = self.parse_response_html(response.text)

        # Add extra fields before returning the results.
        request.meta['user_agent'] = request.headers['User-Agent']
        request.meta['device_type'] = os.environ.get(
            'SCRAPY_DEVICE_TYPE') or 'desktop'
        request.meta['method'] = 'web'
        request.meta['total_locations'] = min(
            len(self.locations),
            self.max_locations if self.max_locations > 0 else sys.maxsize)
        request.meta['tags'] = self.tags

        item['payload'] = {'request': request.meta, 'response': parsed_data}
        item['trace'] = {'proxy': request.meta.get('proxy_id')}

        if self.crawler:
            self.crawler.stats.inc_value('location/%s/pages_count' %
                                         self._location_to_key(location))
            self.crawler.stats.inc_value(
                'location/%s/products_count' % self._location_to_key(location),
                len(parsed_data.get('products')))

        if parsed_data and parsed_data.get('products'):
            yield item

        if not self.get_pages_in_parallel:
            next_request = self._maybe_make_next_request(request, parsed_data)
            if next_request:
                yield next_request

    def parse_response_html(self, html):
        sel = Selector(text=html)
        return parse_search_results(html, sel)

    def _set_proxy_on_request(self, request):
        state_full = self.state_short_to_full_map[request.meta['args']
                                                  ['location']['state']]
        oxylabs_state_name = 'us_' + state_full.lower().replace(' ', '_')

        proxy_session_id = request.meta['proxy_session_id']

        # We are using the same proxy host that will automatically switch
        # the IP based on the location specified in credentials.
        proxy_user = 'customer-%s-cc-US-state-%s' % (self.OXYLABS_USER,
                                                     oxylabs_state_name)
        if self.use_sticky_proxy_session:
            proxy_user += '-sessid-%s' % proxy_session_id
        proxy_password = self.OXYLABS_PASSWORD
        proxy_host_port = 'us-pr.oxylabs.io:10000'
        proxy_id = '%s@%s' % (proxy_user, proxy_host_port)

        # We want to throttle requests based on the location in credentials.
        request.meta['download_slot'] = proxy_id
        request.meta['proxy'] = proxy_host_port

        request.meta['proxy_id'] = proxy_id  # Added for tracing.

        encoded_user_pass = base64.b64encode(
            (proxy_user + ':' + proxy_password).encode('utf-8'))
        request.headers[
            'Proxy-Authorization'] = 'Basic ' + encoded_user_pass.decode(
                'utf-8')

    def _test_anti_robot_response(self, response):
        anti_robot_test = self.check_for_anti_robot_response(response) or {}
        if anti_robot_test.get('detected'):
            proxy = response.request.meta.get('proxy')
            self.log.warning('Anti-robot response detected: %s (proxy: %s)' %
                             (response.request, proxy))
            if self.crawler:
                self.crawler.stats.inc_value('anti_robot/blocked_requests')
            return True
        return False

    def process_failure(self, failure):
        request = failure.request

        proxy_id = request.meta.get('proxy_id')
        self.log.error('Failed request with proxy %s: %s' %
                       (proxy_id, failure.getErrorMessage()))

        location = request.meta['args']['location']
        if self.crawler:
            self.crawler.stats.inc_value(
                'location/%s/items_count' % self._location_to_key(location), 0)


def ad_hoc_test():
    import os
    from pprint import pprint

    file_path = os.path.join(_research_dir,
                             '20191017/Amazon.com_ wooden toys.html')
    print(os.path.abspath(file_path))

    html = None
    with open(file_path, 'r') as content_file:
        html = content_file.read()

    query = 'test query'
    location = {'country': 'US', 'state': 'WA'}

    spider = AmzLocalSearchWebSpider(query)
    spider.crawler = None

    response = HtmlResponse('http://test', status=200, body=html)
    response.request = spider._make_first_request(
        spider._args(query=query,
                     location=location,
                     max_pages=3,
                     tracking_id='test'))

    result = spider.parse_response(response)
    pprint(list(result))


if __name__ == '__main__':
    ad_hoc_test()
