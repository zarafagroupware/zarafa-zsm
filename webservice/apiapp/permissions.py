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


from django_ext.urlresolvers import cached_resolve
from loaders.resources import get_resource
from tastypie_ext.api import Api


class InvalidPermission(Exception):
    def __init__(self, perm_name):
        self.perm_name = perm_name

    def __str__(self):
        return self.perm_name


class Permission(object):
    def __init__(self, name, method, view_type, view_name, resource, urlpat, is_priv=False):
        self.name = name
        self.method = method
        self.view_type = view_type
        self.view_name = view_name
        self.resource = resource
        self.urlpat = urlpat
        self.is_priv = is_priv

    def __repr__(self):
        return '<{0}: {1} {2} {3} {4} {5}>'.format(
            self.__class__.__name__,
            self.name,
            self.method, self.view_name, self.resource._meta.resource_name,
            self.urlpat)


class PermissionStore(object):
    _instance = None

    def __init__(self):
        self._perms = []
        self.resolve_map = {}

        self.api = Api.get_api('v1')
        for resource_obj in self.api._registry.values():
            actions = self.get_actions(resource_obj)

            for tmpl, tup in actions:
                method, view_type, view_name, urlpat, is_priv = tup

                res_name = self.get_resource_display_name(resource_obj)
                name = tmpl.format(res_name)

                perm = Permission(
                    name,
                    method.upper(),
                    view_type,
                    view_name,
                    resource_obj,
                    urlpat,
                    is_priv,
                )

                self._perms.append(perm)

        for perm in self.get_all():
            tup = (perm.method, perm.view_name, perm.resource._meta.resource_name)
            self.resolve_map[tup] = perm

    def get_resource_display_name(self, resource_obj):
        return resource_obj.__class__.__name__.replace('Resource', '')

    def get_actions(self, resource_obj):
        servers = get_resource('api_ldap.ServerResource')
        tenants = get_resource('api_ldap.TenantResource')

        custom_perms = {
            (servers, 'list', 'post'): 'Create{0}',
            (tenants, 'list', 'post'): 'Create{0}',
        }

        method_map = dict(
            delete='Write{0}',
            get='View{0}',
            post='Write{0}',
            put='Write{0}',
            patch='Write{0}',
        )

        suffix_map = dict(
            acl='Acl',
            privs='Privileges',
        )

        actions = []

        for _, viewmeta in resource_obj.viewregistry.get_all():
            for method in viewmeta.get_methods():
                is_priv = True
                perm_tmpl = custom_perms.get((resource_obj, viewmeta.name, method))

                if not perm_tmpl:
                    is_priv = False
                    perm_tmpl = method_map.get(method)

                    perm_suffix = suffix_map.get(viewmeta.name)
                    if perm_suffix:
                        perm_tmpl = '{0}{1}'.format(perm_tmpl, perm_suffix)

                view_type = viewmeta.name
                view_name = resource_obj.get_view_name(viewmeta.name)
                tmpl_uri = viewmeta.get_template_uri(resource_obj)

                tup = (perm_tmpl, (method, view_type, view_name, tmpl_uri, is_priv))
                actions.append(tup)

        return actions

    @classmethod
    def get(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def get_all(self):
        return self._perms

    def get_all_names(self, is_priv=False, is_acl=False):
        names = []

        if is_priv:
            names = [p.name for p in self._perms if p.is_priv]
        elif is_acl:
            names = [p.name for p in self._perms if not p.is_priv]
        else:
            names = [p.name for p in self._perms]

        names = sorted(list(set(names)))

        return names

    @classmethod
    def filter_valid(cls, perms):
        all_perms = cls.get().get_all_names()
        perms = list(set(perms).intersection(set(all_perms)))
        return perms

    def resolve(self, request, resource_obj):
        path = request.META.get('PATH_INFO')
        if path:
            match = cached_resolve(path)

            tup = (
                request.method.upper(),
                match.view_name,
                resource_obj._meta.resource_name,
            )
            perm = self.resolve_map.get(tup)

            return perm, match


def resolve(request, resource_obj):
    store = PermissionStore.get()
    return store.resolve(request, resource_obj)
