#!/usr/bin/env python

import sys
sys.path.append('..')

import logging
import time

from libzsm.rest_client.api import Api
from libzsm.rest_client.logutils import get_logger


API_BASE_URL = 'http://zarvm:80/api/v1/'
ORIGIN_TENANT_NAME = 'origin'
ORIGIN_ADMIN_USERNAME = 'admin'
ORIGIN_ADMIN_PASSWORD = 'a'

TENANT = 'cloudy.com'
SERVER = 'zarafa1'


class UserGen(object):
    def __init__(self):
        self.api = Api(
            API_BASE_URL,
            basic_auth=(
                u'{0}@{1}'.format(
                    ORIGIN_ADMIN_USERNAME,
                    ORIGIN_TENANT_NAME,
                ),
                ORIGIN_ADMIN_PASSWORD,
            )
        )

        if '-v' in sys.argv:
            logger = get_logger(__file__)
            logger.setLevel(logging.DEBUG)

        self.server = self.api.get_server(name=SERVER)
        self.tenant = self.api.get_tenant(name=TENANT)

    def create(self, name):
        initial = {
            'mail': '%s@example.com' % name,
            'name': name,
            'surname': name,
            'tenant': self.tenant,
            'userServer': self.server,
            'username': name,
        }

        self.api.create_user(initial=initial)

        return self.api.last_apireq.response

    def run(self):
        for i in xrange(2100, 12000):
            name = 'user%s' % i
            pre = time.time()
            response = self.create(name)
            print(u'HTTP %s, took %.2fs' % (response.status_code, time.time() - pre))


if __name__ == '__main__':
    usergen = UserGen()
    usergen.run()
