import os
import pytest

from bb_scraping.proxy.simple_provider import SimpleProxyProvider
from bb_scraping.proxy.base import ProxyError

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
RESOURCES_DIR = os.path.join(SCRIPT_DIR, 'resources')


def _resource_path(fn):
    return os.path.join(RESOURCES_DIR, fn)


@pytest.fixture(scope="module")
def provider():
    return SimpleProxyProvider.from_disk(
        proxies_path=_resource_path('test-proxy-list.txt'),
        config_path=_resource_path('test-proxy-config.yaml'))


def test_simple_provider(provider):
    proxies = provider.get_proxies_for('amazon.com:user:buzgene@gmail.com')
    assert str(proxies[0]) == 'http://23.95.173.169:13228'


def test_get_proxy_by_id(provider):
    proxy = provider.get_proxy_by_id('http://23.95.173.169:13228')
    assert str(proxy) == 'http://23.95.173.169:13228'


def test_exception_when_invalid_id_requested(provider):
    with pytest.raises(ProxyError, match=r'Cannot find a proxy .*'):
        provider.get_proxy_by_id('000.000.000.000')
