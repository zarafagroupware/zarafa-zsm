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


from django.utils import importlib

from apiapp.tastypie_ext.api import Api


class ResourceCache(object):
    def __init__(self):
        self._instance_cache = {}
        self._class_cache = {}

    @property
    def api(self):
        if not getattr(self, '_api', None):
            self._api = Api.get_api('v1')
        return self._api

    def get_resource(self, name):
        resource = self._instance_cache.get(name)

        if not resource:
            resource_class = self.get_resource_class(name)
            resource = [res for res in self.api._registry.values()
                        if isinstance(res, resource_class)][0]
            self._instance_cache[name] = resource

        return resource

    def get_resource_class(self, name):
        parts = name.split('.')
        if not 'apiapp' == parts[0]:
            parts.insert(0, 'apiapp')

        name = '.'.join(parts)

        resource_class = self._class_cache.get(name)

        if not resource_class:
            resource_name = parts[-1]
            resource_path = '.'.join(parts[:-1])

            module = importlib.import_module(resource_path)
            resource_class = getattr(module, resource_name)

            self._class_cache[name] = resource_class

        return resource_class


resource_cache = ResourceCache()

get_resource = resource_cache.get_resource
get_resource_class = resource_cache.get_resource_class
