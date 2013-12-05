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


from libzsm.datehelper import format_dt
from libzsm.datehelper import parse_str
from libzsm.uri import url_to_path

from exc import InvalidAttributeValue
from model import Model


class Field(object):
    def __init__(self, schema, name, field_dct):
        self.schema = schema
        self.name = name

        for f in ['blank', 'default', 'example', 'help_text', 'nullable', 'readonly',
                  'signature', 'type', 'unique']:
            val = field_dct.get(f)
            setattr(self, f, val)

    def __repr__(self):
        return "<{0}: {1}>".format(self.__class__.__name__, self.name)

    def deserialize_value(self, value):
        if self.type == 'related':
            if value:
                func = self.schema.resource.api.get_model_instance_by_path
                if type(value) == list:
                    value = [func(v) for v in value]
                else:
                    value = func(value)

        elif value and self.type == 'datetime':
            value = parse_str(value)

        return value

    def serialize_related_value(self, value):
        if isinstance(value, basestring):
            return unicode(value)

        elif isinstance(value, Model):
            return unicode(url_to_path(value.base_url))

    def serialize_value(self, value):
        if value is None:
            if not self.nullable:
                raise InvalidAttributeValue(self.name, value)
            return value

        else:
            try:
                if self.type == 'string':
                    return unicode(value)
                elif self.type == 'boolean':
                    return bool(value)
                elif self.type == 'datetime':
                    return format_dt(value)
                elif self.type == 'integer':
                    return int(value)
                elif self.type == 'list':
                    return list(value)
                elif self.type == 'related':
                    if type(value) == list:
                        return [self.serialize_related_value(v) for v in value]
                    else:
                        return self.serialize_related_value(value)

            except (TypeError, ValueError):
                raise InvalidAttributeValue(self.name, value)


class View(object):
    def __init__(self, name):
        self.name = name
        self.operations = {}

    def add_operation(self, viewop):
        self.operations[viewop.method.lower()] = viewop

    def get(self, method):
        return self.operations.get(method)


class ViewOperation(object):
    def __init__(self, method, perm, urlpat, relpath=None):
        self.method = method
        self.perm = perm
        self.urlpat = urlpat
        self.relpath = relpath


class Schema(object):
    def __init__(self, resource, url, schema_dct):
        self.resource = resource
        self.url = url
        self.fields = {}
        self.views = {}

        for fieldname, dct in schema_dct.get('fields', {}).items():
            self.fields[fieldname] = Field(self, fieldname, dct)

        for name, items in schema_dct.get('views', {}).items():
            view = View(name)
            for item in items:
                viewop = ViewOperation(
                    item.get('method'),
                    item.get('permission'),
                    item.get('urlPattern'),
                    item.get('detailRelativePath'),
                )
                view.add_operation(viewop)
            self.views[name] = view

    @property
    def base_url(self):
        return self.url

    def __repr__(self):
        return "<{0}: {1}>".format(self.__class__.__name__, self.base_url)
