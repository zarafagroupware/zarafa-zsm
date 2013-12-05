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


import re


class InvalidApiBaseUrl(Exception):
    def __init__(self, url):
        self.url = url

    def __str__(self):
        return "{0}: {1}".format(self.__class__.__name__, self.url)


class InvalidEndpoint(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "{0}: {1}".format(self.__class__.__name__, self.name)


class InvalidView(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "{0}: {1}".format(self.__class__.__name__, self.name)


class InvalidAttribute(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "{0}: {1}".format(self.__class__.__name__, self.name)


class InvalidAttributeValue(Exception):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __str__(self):
        return "{0} for attribute {1} with value: {2}".format(
            self.__class__.__name__, self.name, repr(self.value)
        )


class ObjectDoesNotExist(Exception):
    pass

class MultipleObjectsReturned(Exception):
    pass


class HttpException(Exception):
    pass

class Http400(HttpException):
    pass

class Http401(HttpException):
    pass

class Http403(HttpException):
    pass

class Http404(HttpException):
    pass

class Http405(HttpException):
    pass

class Http411(HttpException):
    pass

class Http500(HttpException):
    pass

_http_excs = {}

def build_http_exc_map():
    global _http_excs
    for key, val in globals().items():
        m = re.search('^Http([0-9]{3})$', key)
        if m:
            code = int(m.group(1))
            _http_excs[code] = val

build_http_exc_map()

def get_http_exc(status_code):
    global _http_excs
    return _http_excs[status_code]
