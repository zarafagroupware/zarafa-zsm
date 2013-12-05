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


import copy
import json

from requests import Request
from requests import Session

from exc import get_http_exc
from logutils import format_request
from logutils import format_response
import logutils

logger = logutils.get_logger(__file__)


class ApiRequest(object):
    def __init__(self, url, data=None, method='get', auth=None):
        self.url = url
        self.data = data
        self.method = method
        self.auth = auth

        self.encoding = 'utf-8'
        self.skip_serialize = False

        self.standard_headers = {
            'Accept': 'application/json',
        }

        self.session = None
        self.request = None
        self.response = None

    def serialize_data(self):
        '''NOTE: It's important to return an empty string when no data is sent,
        not None. As that causes requests to interpret the payload as
        a stream and set the wrong headers (Transfer-Encoding: chunked).'''
        data = ''
        if self.data:
            data = json.dumps(self.data, indent=2,
                              sort_keys=True, ensure_ascii=False)
            data = data.encode('utf-8')

        return data

    def deserialize_response(self, response):
        dct = {}
        try:
            dct = json.loads(response.text) if response.text else {}
        except ValueError:
            logger.warn(u'Failed to deserialized response:\n{0}'.format(response.text))
        return dct

    def get_headers(self):
        headers = copy.copy(self.standard_headers)
        # only needed when transmitting data
        if self.data:
            charset = 'charset={0}'.format(self.encoding)
            headers.update({
                'Content-Type': 'application/json; {0}'.format(charset),
            })
        return headers

    def is_error(self, response):
        return 400 <= response.status_code < 600

    def perform(self):
        data = self.data
        if not self.skip_serialize:
            data = self.serialize_data()

        headers = self.get_headers()

        self.session = Session()
        self.request = Request(url=self.url, method=self.method.upper(),
                               headers=headers, data=data, auth=self.auth)
        self.request = self.request.prepare()
        self.request.encoding = self.encoding

        logger.debug(u'Making request:\n{0}'.format(format_request(self.request)))
        self.response = self.session.send(self.request)

        logger.debug(u'Received response:\n{0}'.format(format_response(self.response)))

        dct = {}

        content_type = self.response.headers.get('content-type')
        if content_type.startswith('application/json'):
            dct = self.deserialize_response(self.response)

        if self.is_error(self.response):
            exc_class = get_http_exc(self.response.status_code)
            raise exc_class(dct)

        return dct
