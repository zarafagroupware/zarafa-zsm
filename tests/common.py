# Copyright 2012 - 2013  Zarafa B.V.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3,
# as published by the Free Software Foundation with the following additional
# term according to sec. 7:
#
# According to sec. 7 of the GNU Affero General Public License, version
# 3, the terms of the AGPL are supplemented with the following terms:
#
# "Zarafa" is a registered trademark of Zarafa B.V. The licensing of
# the Program under the AGPL does not imply a trademark license.
# Therefore any rights, title and interest in our trademarks remain
# entirely with us.
#
# However, if you propagate an unmodified version of the Program you are
# allowed to use the term "Zarafa" to indicate that you distribute the
# Program. Furthermore you may use our trademarks where it is necessary
# to indicate the intended purpose of a product or service provided you
# use it in accordance with honest practices in industrial or commercial
# matters.  If you want to propagate modified versions of the Program
# under the name "Zarafa" or "Zarafa Server", you may only do so if you
# have a written permission by Zarafa B.V. (to acquire a permission
# please contact Zarafa at trademark@zarafa.com).
#
# The interactive user interface of the software displays an attribution
# notice containing the term "Zarafa" and/or the logo of Zarafa.
# Interactive user interfaces of unmodified and modified versions must
# display Appropriate Legal Notices according to sec. 5 of the GNU
# Affero General Public License, version 3, when you propagate
# unmodified or modified versions of the Program. In accordance with
# sec. 7 b) of the GNU Affero General Public License, version 3, these
# Appropriate Legal Notices must retain the logo of Zarafa or display
# the words "Initial Development by Zarafa" if the display of the logo
# is not reasonably feasible for technical reasons. The use of the logo
# of Zarafa in Legal Notices is allowed for unmodified and modified
# versions of the software.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
if sys.version_info < (2, 7):
    from unittest2 import TestCase
else:
    from unittest import TestCase  # NOQA

import logging
import sys
import uuid

from libzsm.rest_client.logutils import get_logger
from libzsm.rest_client.utils import get_api
from libzsm.text import get_random_unistr

from webservice.conf.settings import config


def get_random_name():
    random_name = u'{0}'.format(uuid.uuid4().hex[5:13])
    random_name = list(random_name)
    random_name[4:4] = get_random_unistr(8)
    random_name = u''.join(random_name)
    return random_name


class ApiTestBase(TestCase):
    def __init__(self, *args, **kwargs):
        super(ApiTestBase, self).__init__(*args, **kwargs)

        # a bit hacky, set the logger level if we have -v
        if '-v' in sys.argv:
            logger = get_logger(__file__)
            logger.setLevel(logging.DEBUG)

        self.api = get_api()

    @property
    def server1(self):
        if not getattr(self, '_server1', None):
            self._server1 = self.api.get_server(name=config.ZARAFA_SERVER1_NAME)
        return self._server1

    def verify_model_attributes(self, model, atts):
        for key, fixture_val in atts.items():
            model_val = getattr(model, key)

            # if the value is a list, sort it
            if type(fixture_val) == list:
                fixture_val.sort()
            if type(model_val) == list:
                model_val.sort()

            self.assertEqual(
                fixture_val, model_val,
                msg=u'{0}: {1} != {2}'.format(key, fixture_val, model_val))

    def verify_iterable(self, fixture, other):
        if type(fixture) == list:
            fixture.sort()

        if type(other) == list:
            other.sort()

        self.assertEqual(fixture, other)
