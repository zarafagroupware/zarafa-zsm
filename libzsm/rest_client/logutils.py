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
import os


formatter = logging.Formatter('%(asctime)s %(name)-8s %(levelname)-6s %(message)s')

_logger = None

CHATTY_LOGGERS = [
    'apirequest',
    'requests',
]


# python 2.7
class NullHandler(logging.Handler):
    def createLock(self):
        self.lock = None

    def handle(self, record):
        pass

    def emit(self, record):
        pass


def get_logger(name, level=logging.WARN):
    global _logger

    if re.search('[./]', name):
        name = os.path.basename(name)
        name, _ = os.path.splitext(name)

    if not _logger:
        _logger = logging.getLogger(name)
        _logger.setLevel(level)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        _logger.addHandler(stream_handler)

        # remove propagation for chatty nested loggers
        for pkgname, logger in _logger.manager.loggerDict.items():
            for pkgpat in CHATTY_LOGGERS:
                if pkgpat in pkgname:
                    # fix requests.packages.urllib3.connectionpool complaining
                    # about missing handler
                    if not getattr(logger, 'handlers', None):
                        if hasattr(logger, 'addHandler'):
                            logger.addHandler(NullHandler())

                    logger.propagate = False

    return _logger

def format_request(request):
    s = u'{0} {1}'.format(request.method, request.url)

    if request.headers:
        for key, val in sorted(request.headers.items()):
            s += u'\n{0}: {1}'.format(key.title(), val)
        s += u'\n'

    if request.body:
        s += u'\n{0}'.format(request.body.decode(request.encoding))

    return s

def format_response(response):
    reason = getattr(getattr(response.raw, '_original_response', None), 'reason', '')
    s = u'HTTP {0} {1}'.format(response.status_code, reason)

    if response.headers:
        for key, val in sorted(response.headers.items()):
            s += u'\n{0}: {1}'.format(key.title(), val)
        s += u'\n'

    if response.text:
        s += u'\n{0}'.format(response.text)

    return s
