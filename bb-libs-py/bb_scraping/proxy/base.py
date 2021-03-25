###############################################################################
# Copyright (c) BB Studio. All Rights Reserved.
###############################################################################


class ProxyError(Exception):
    def __init__(self, msg):
        super(ProxyError, self).__init__(msg)


class ProxyNotFound(ProxyError):
    def __init__(self, msg):
        super(ProxyNotFound, self).__init__(msg)


class Proxy:
    def __init__(self, host, port, user=None, password=None,
                 proxy_type=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

        if proxy_type is None:
            proxy_type = 'http'
        self.proxy_type = proxy_type

    @classmethod
    def from_url(cls, url):
        from six.moves.urllib.parse import urlparse

        url = url.strip()
        if '://' not in url:
            url = 'http://' + url

        parsed = urlparse(url)
        if not parsed.hostname or not parsed.port:
            raise ProxyError('Cannot parse proxy url: %s' % url)

        return Proxy(parsed.hostname, parsed.port, parsed.username,
                     parsed.password, parsed.scheme)

    def to_url(self, include_creds=True):
        maybe_creds = ''
        if self.user and include_creds:
            maybe_creds = '%s:%s@' % (self.user, self.password)

        return '%s://%s%s:%d' % \
            (self.proxy_type, maybe_creds, self.host, self.port)

    @property
    def id(self):
        return self.to_url(include_creds=False)

    def __str__(self):
        return self.to_url(include_creds=False)

    def __repr__(self):
        return self.__str__()
