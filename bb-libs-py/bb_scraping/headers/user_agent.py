##############################################################################
# Copyright (c) BB Studio. All Rights Reserved.
##############################################################################

import os
import random

_script_dir = os.path.dirname(os.path.realpath(__file__))
_resources_dir = os.path.join(_script_dir, 'resources')


class SampleUserAgent:
    DESKTOP_OSX_SAFARI = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) ' \
                         'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         'Chrome/64.0.3282.167 Safari/537.36'

    DESKTOP = DESKTOP_OSX_SAFARI


def _resource_path(fn):
    return os.path.join(_resources_dir, fn)


class UserAgentProvider(object):
    def __init__(self, user_agents):
        self.user_agents = user_agents
        self.next_agent_idx = 0

        random.shuffle(self.user_agents)

    def next(self):
        item = self.user_agents[self.next_agent_idx]
        self.next_agent_idx = ((self.next_agent_idx + 1) %
                               len(self.user_agents))
        return item

    @classmethod
    def load_desktop(cls):
        return cls.from_disk(_resource_path('ua-desktop.txt'))

    @classmethod
    def load_mobile(cls):
        return cls.from_disk(_resource_path('ua-mobile.txt'))

    @classmethod
    def from_disk(cls, user_agents_path=None):
        if user_agents_path is None:
            user_agents_path = _resource_path('ua-desktop.txt')

        user_agents = []
        with open(user_agents_path) as f:
            for line in f:
                line = line.strip()
                if len(line) > 0 and not line.startswith('#'):
                    user_agents.append(line)
        return UserAgentProvider(user_agents)


if __name__ == '__main__':
    from pprint import pprint

    user_agents_source = UserAgentProvider.from_disk()
    pprint(user_agents_source.next())

    pprint(SampleUserAgent.DESKTOP)
