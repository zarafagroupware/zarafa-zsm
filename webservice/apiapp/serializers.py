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

from django.core.exceptions import ValidationError
from django.core.serializers import json
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.utils.encoding import DjangoUnicodeDecodeError

from tastypie.serializers import Serializer


class PrettyJSONSerializer(Serializer):
    json_indent = 2
    rx_underscore = re.compile('([_])([a-zA-Z])')
    rx_camelcase = re.compile('([a-z])([A-Z])')
    # we need an explicit list because we can't uncamelize all keys blindly,
    # it will break resources
    camelize_keys = ['resource_uri']

    def __init__(self, enable_camelizer=True, *args, **kwargs):
        super(PrettyJSONSerializer, self).__init__(*args, **kwargs)

        self.enable_camelizer = enable_camelizer

        self.uncamelize_keys = []
        for key in self.camelize_keys:
            k = self.camelize(key)
            self.uncamelize_keys.append(k)

    ## Traversals

    def camelize(self, key):
        if key in self.camelize_keys:
            key = re.sub(
                self.rx_underscore,
                lambda m: m.group(2).upper(),
                key,
            )
        return key

    def uncamelize(self, key):
        if key in self.uncamelize_keys:
            key = re.sub(
                self.rx_camelcase,
                lambda m: '{0}_{1}'.format(m.group(1), m.group(2).lower()),
                key,
            )
        return key

    def traverse(self, data, apply_func):
        '''NOTE: Mutates the value.'''

        if isinstance(data, dict):
            for key, value in data.items():
                key_new = apply_func(key)

                if not isinstance(value, basestring):
                    # only apply if it's a nested object
                    value = self.traverse(value, apply_func)

                data[key_new] = value
                if not key == key_new:
                    data.pop(key, None)

        elif isinstance(data, list):
            return [self.traverse(i, apply_func) for i in data]

        return data

    ## Serialization

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)

        if self.enable_camelizer:
            data = self.traverse(data, self.camelize)

        return simplejson.dumps(data, cls=json.DjangoJSONEncoder,
                                sort_keys=True, ensure_ascii=False,
                                indent=self.json_indent)

    def from_json(self, content, encoding='utf-8'):
        # pass unicode to deserializer so we get unicode back
        try:
            content = smart_unicode(content, encoding=encoding)
        except DjangoUnicodeDecodeError:
            raise ValidationError(u'Could not decode string as {0}'.format(encoding))

        data = super(PrettyJSONSerializer, self).from_json(content)

        if self.enable_camelizer:
            data = self.traverse(data, self.uncamelize)

        return data
