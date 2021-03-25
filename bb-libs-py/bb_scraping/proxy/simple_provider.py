##############################################################################
# Copyright (c) BB Studio. All Rights Reserved.
##############################################################################

import logging
import os
import random

from bb_utils.base.exceptions import ArgumentError
from bb_scraping.proxy.base import (Proxy, ProxyError)

_script_dir = os.path.dirname(os.path.realpath(__file__))
_resources_dir = os.path.join(_script_dir, 'resources')


##############################################################################
# Helpers
##############################################################################

def _resource_path(fn):
    return os.path.join(_resources_dir, fn)


def _index(proxies, dic=None):
    if dic is None:
        dic = {}

    count = 0
    for p in proxies:
        dic[p.id] = p
        count += 1

    logging.debug('Indexed %d entries' % count)
    return dic


def _enum_proxies_from_stream(fs):
    logging.debug('Loading proxy files...')
    for line in fs:
        line = line.strip()

        if line.startswith('#') or len(line) == 0:
            continue

        yield Proxy.from_url(line)


def _read_config(fs):
    import yaml
    return yaml.load(fs)


def _as_list(item):
    if item is None:
        return None

    if isinstance(item, list):
        return item

    return [item]


##############################################################################
# Constants
##############################################################################

ALL_PROXIES_TAG = 'ALL'


##############################################################################
# Simple config provider
##############################################################################

class SimpleProxyConfig(object):
    def __init__(self, proxies_stream=None, config_stream=None):
        self.proxies = {}
        self.loaded = False

        self._load(proxies_stream, config_stream)

    @classmethod
    def from_disk(cls, proxies_path=None, config_path=None):
        if proxies_path is None:
            raise ArgumentError("Proxy file is not specified.")

        proxies_stream = None
        config_stream = None

        try:
            proxies_stream = open(proxies_path)
            if config_path:
                config_stream = open(config_path)

            return SimpleProxyConfig(proxies_stream, config_stream)
        finally:
            if config_stream:
                config_stream.close()

            if proxies_stream:
                proxies_stream.close()

    def _load(self, proxies_stream, config_stream):
        # Load config
        #

        self.config = _read_config(config_stream) if config_stream else {}

        # Load all proxies
        #

        self.proxies = {}
        self.proxies[ALL_PROXIES_TAG] = \
            _index(_enum_proxies_from_stream(proxies_stream))

        # Index proxy profiles
        #

        self._load_profiles()

    def _load_profiles(self):
        for profile in self.config.get('profiles', []):
            self._index_profile(profile)

    def _index_profile(self, profile):
        all_proxies = self.proxies[ALL_PROXIES_TAG]

        for tag in _as_list(profile['tag']):
            # Get existing proxies for this tag or create a new
            # collection.
            profile_proxies = self.proxies.get(tag, {})
            self.proxies[tag] = profile_proxies
            
            # Index proxies assigned to profile.
            if profile['proxies'] == ALL_PROXIES_TAG:
                profile_proxies.update(all_proxies)
            else:
                for proxy in profile['proxies']:
                    profile_proxies[proxy] = all_proxies[proxy]

            # Remove assigned proxies from requested profile.
            # Referenced profiles must already be defined. It is expected that
            # such profiles will contain only a few proxies to remove.
            if 'remove_from' in profile:
                for proxy in profile_proxies:
                    for another_profile_sel in profile['remove_from']:
                        if proxy in self.proxies[another_profile_sel]:
                            del self.proxies[another_profile_sel][proxy]


##############################################################################
# Simple proxy provider
##############################################################################

class SimpleProxyProvider(object):

    def __init__(self, config):
        self.proxies = config.proxies

    @classmethod
    def from_disk(cls, proxies_path=None, config_path=None):
        return SimpleProxyProvider(SimpleProxyConfig.from_disk(
            proxies_path, config_path))

    def get_proxies_for(self, tag=None):
        if tag is None:
            tag = ALL_PROXIES_TAG

        if tag in self.proxies:
            return self.proxies[tag].values()
        else:
            raise ProxyError(
                'Cannot find a proxy collection matching <%s>' % tag)

    def get_proxy_for(self, tag=None):
        return random.choice(self.get_proxies_for())

    def get_proxy_by_id(self, proxy_id, tag=None, raise_if_not_found=True):
        if tag is None:
            tag = ALL_PROXIES_TAG

        proxy = None
        if tag in self.proxies:
            proxy = self.proxies[tag].get(proxy_id)

        if proxy:
            return proxy
        elif raise_if_not_found:
            raise ProxyError(
                'Cannot find a proxy with id <%s> and tag <%s>'
                % (proxy_id, tag))


##############################################################################
# Ad hoc tests
##############################################################################

if __name__ == '__main__':
    from pprint import pprint

    logging.basicConfig(level=logging.DEBUG)

    provider = SimpleProxyProvider.from_disk(
        config_path=_resource_path('config-test.yaml'))

    pprint(provider.get_proxy_for('amazon.com:user:buzgene@gmail.com'))
    pprint(provider.get_proxy_by_id('23.95.14.183'))
