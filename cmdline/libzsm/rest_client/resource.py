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


from libzsm.uri import url_to_host
from libzsm.uri import urljoin

from model import Model
from schema import Schema


class Resource(object):
    def __init__(self, api, resource_name,
                 relative_path, schema_url, apidoc_url,
                 parent=None, children=None):
        self.api = api
        self.apidoc_url = apidoc_url
        self.relative_path = relative_path
        self.resource_name = resource_name
        self.schema_url = schema_url

        self.children = children or {}
        self.parent = parent

        self.id_attribute = 'id'

        from libzsm import text
        self.model_class = Model.get_class(text.make_singular(resource_name))
        self.model_class._resource = self

    def get_list_uri(self, model_instance_parent=None):
        parts = []

        if model_instance_parent:
            parts = [
                model_instance_parent.base_url,
                self.relative_path,
            ]
        else:
            parts = [
                self.api.base_url,
                self.relative_path,
            ]

        return urljoin(*parts)

    def get_detail_uri(self, model_instance):
        parts = []

        if self.parent:
            param_name = self.parent.singular_name

            # bypass fetch hook and just grab the url directly
            parent_path = model_instance.get_bound().get(param_name)
            assert parent_path is not None
            host = url_to_host(self.api.base_url)
            parent_url = urljoin(host, parent_path)

            parts = [
                parent_url,
                self.relative_path,
                getattr(model_instance, self.id_attribute),
            ]

        else:
            parts = [
                self.api.base_url,
                self.relative_path,
                getattr(model_instance, self.id_attribute),
            ]

        return urljoin(*parts)

    @property
    def schema(self):
        schema = getattr(self, '_schema', None)

        if not schema:
            dct = self.api.call_api(self.schema_url)
            schema = Schema(self, self.schema_url, dct)
            self._schema = schema

        return schema

    @property
    def plural_name(self):
        from libzsm import text
        return text.make_plural(self.resource_name)

    @property
    def singular_name(self):
        from libzsm import text
        return text.make_singular(self.resource_name)
