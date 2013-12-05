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


import logging
import re

from django.conf import settings as djsettings
from django.http import HttpResponse
from django.template.loader import render_to_string

from libzsm.http import get_code_desc

from authentication import has_auth_token
from conf.settings import config
from serializers import PrettyJSONSerializer
from tastypie_ext.api import Api

logger = logging.getLogger(__file__)


RAW_OUTPUT_HEADER = 'HTTP_X_RAW_OUTPUT'

class DefaultFormatSelectorMiddleware(object):
    '''Tastypie determines the format based on:
        * a ?format= param
        * the Accept: header
       Browsers tend to send Accept: text/html, which is not a suppported
       format and makes debugging in the browser inconvenient. Here we
       rewrite the Accept header to json.'''

    def process_request(self, request):
        accept = request.META.get('HTTP_ACCEPT')

        required = 'application/json'

        if not accept or not required in accept:
            accept = accept or ''
            encs = accept.split(',')

            # move html to the back if it's in the list
            if 'text/html' in encs[0]:
                encs.pop(0)
                encs.append('text/html')

            # insert json at the head
            encs.insert(0, required)

            accept = ','.join(encs)
            request.META['HTTP_ACCEPT'] = accept

        # convert ?raw param to a header, to hide it from the webapp
        raw = request.GET.get('raw')
        if raw:
            GET = request.GET.copy()
            GET.pop('raw', None)
            request.GET = GET
            request.META[RAW_OUTPUT_HEADER] = 1


class PrettyPrintMiddleware(object):
    def __init__(self):
        self.serializer = PrettyJSONSerializer(enable_camelizer=False)

    def is_enabled(self, request):
        if request.META.get(RAW_OUTPUT_HEADER):
            return False

        if not getattr(config, 'ENABLE_API_DEBUG_VIEW', False):
            return False

        accept = request.META.get('HTTP_ACCEPT')
        if accept and not 'text/html' in accept:
            return False

        # check HTTP_X_REQUESTED_WITH == XMLHttpRequest
        if request.is_ajax():
            return False

        return True

    def is_json(self, response):
        for key, value in response.items():
            if key == 'Content-Type' and value.startswith('application/json'):
                return True

    def pass_through(self, request, response):
        '''Whether to let the response pass through verbatim.'''

        # Yes if it's a redirect
        if 300 <= response.status_code < 400:
            return True

        # Yes if response is 401 and browser has not yet authenticated
        if response.status_code == 401 and not has_auth_token(request):
            return True

        # Not if it's an error that should always be rendered
        if response.status_code in [404, 500]:
            return False

        # Not if it's empty
        if not response.content.strip():
            return False

        # Not if it's json
        if self.is_json(response):
            return False

        return True

    def deserialize(self, response):
        try:
            content = response.content.decode('utf8')
            if content:
                return self.serializer.from_json(content)
        except Exception as e:
            logger.exception(e)

    def serialize(self, pyobj):
        return self.serializer.to_json(pyobj)

    def get_doc_name(self, pyobj):
        name = ''
        if type(pyobj) == dict:
            name = pyobj.get('name', name)
            if not name:
                keys = [k for k in pyobj.keys() if re.search('(?i)name', k)]
                name = pyobj.get(keys[0], name) if keys else name
        return name

    def make_anchor(self, match):
        url = match.group(0)

        # skip urls with variables, they are patterns only
        if re.search('[{].*[}]', url):
            return url

        return u'<a href="{0}">{1}</a>'.format(url, url)


    def process_response(self, request, response):
        ## Bail out early if we're not supposed to modify the response
        if not self.is_enabled(request):
            return response
        if self.pass_through(request, response):
            return response

        ## Attempt to parse the response as json
        pyobj = self.deserialize(response)

        # render a new page
        js = self.serialize(pyobj) if pyobj is not None else ''

        api = Api.get_api('v1')

        status_desc = get_code_desc(response.status_code)

        html = render_to_string('apiapp/debug_middleware.html', {
            'STATIC_URL': djsettings.STATIC_URL,
            'api': api,
            'json': js,
            'request': request,
            'status_code': response.status_code,
            'status_code_msg': status_desc,
            'title': self.get_doc_name(pyobj),
        })

        ## Anchorize html-ized json
        exclude_anchorize = ['_schema']

        anchorize = True
        for pat in exclude_anchorize:
            if pat in request.get_full_path():
                anchorize = False

        if anchorize:
            html = re.sub('(?<=&quot;)/api/.*?(?=&quot;)', self.make_anchor, html)

        ## Construct new response
        resp = HttpResponse(html, status=response.status_code)

        return resp


class ApiDebugMiddleware(DefaultFormatSelectorMiddleware, PrettyPrintMiddleware):
    pass
