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


import json

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View

from tastypie.exceptions import ImmediateHttpResponse
from tastypie.exceptions import NotFound

from acl import Ace
from acl import Acl
from acl import Privileges
from loaders.models import get_model
from loaders.resources import get_resource
from permissions import PermissionStore
from tastypie_ext.api import Api


class ApiView(View):
    # Common response params
    mimetype = 'application/json'
    status_validation_error = 400
    status_get_ok = 200
    status_created = 201
    status_accepted = 202


class ResourceView(ApiView):
    must_authenticate = True
    must_authorize = True
    methods = ['get']
    resource = None

    def __init__(self, *args, **kwargs):
        atts = ['must_authenticate', 'must_authorize', 'resource']
        for att in atts:
            val = kwargs.get(att)
            if val is not None:
                setattr(self, att, val)

        if not self.resource:
            raise ImproperlyConfigured('Must provide a resource object')

    def dispatch(self, request, *args, **kwargs):
        # Run prolog
        self.resource.method_check(request, allowed=self.methods)

        if self.must_authenticate:
            self.resource.is_authenticated(request)

            if self.must_authorize:
                self.resource.is_authorized(request)

        # Dispatch to view proper
        return self.get_response(request, *args, **kwargs)

    def get_object(self, request, *args, **kwargs):
        group_name = self.resource.get_uri_pk_group_name()
        id = kwargs.get(group_name)
        model = self.resource._meta.object_class

        obj = model.get_object('zarafaId', id)
        if not obj:
            raise NotFound

        return obj


class ResourceAclView(ResourceView):
    methods = ['get', 'put']

    def __init__(self, *args, **kwargs):
        super(ResourceAclView, self).__init__(*args, **kwargs)

        # store objects looked up during validation
        self._objcache = {}

    def get_response(self, request, *args, **kwargs):
        obj = self.get_object(request, *args, **kwargs)

        if request.method == 'PUT':
            return self.put(request, obj)

        return self.get(obj)

    def get(self, obj):
        Group = get_model('models_ldap.Group')
        User = get_model('models_ldap.User')
        res_groups = get_resource('api_ldap.GroupResource')
        res_users = get_resource('api_ldap.UserResource')

        acl_val = getattr(obj, 'zarafaACL', None)

        lst = []
        if acl_val:
            acl = Acl.parse(obj.zarafaACL)

            for ace in acl.aces:
                principal_key = None
                principal = None
                uri = None

                if ace.user_id:
                    principal_key = 'user'
                    principal = User.get_object('zarafaId', ace.user_id)
                    uri = res_users.get_resource_uri(principal)

                elif ace.group_id:
                    principal_key = 'group'
                    principal = Group.get_object('zarafaId', ace.group_id)
                    uri = res_groups.get_resource_uri(principal)

                dct = {
                    principal_key: uri,
                    'permissions': sorted(ace.perms),
                }

                lst.append(dct)

        content = self.resource._meta.serializer.to_json(lst)
        return HttpResponse(content, mimetype=self.mimetype)

    def put(self, request, obj):
        data = json.loads(request.body)
        self.validate(data)

        aces = []
        for d in data:
            perms = d.get('permissions')

            group_uri = d.get('group')
            user_uri = d.get('user')

            kwargs = {}
            if group_uri:
                principal = self._objcache.get(group_uri)
                kwargs['group_id'] = principal.zarafaId

            elif user_uri:
                principal = self._objcache.get(user_uri)
                kwargs['user_id'] = principal.zarafaId

            ace = Ace(perms, **kwargs)
            aces.append(ace)

        acl = Acl(aces)
        obj.zarafaACL = acl.format()
        obj.save()

        resp = self.get(obj)
        resp.status_code = self.status_accepted
        return resp

    def validate(self, data):
        res_groups = get_resource('api_ldap.GroupResource')
        res_users = get_resource('api_ldap.UserResource')

        dct = {}
        invalid_groups = set()
        invalid_perms = set()
        invalid_users = set()
        type_correct = False

        permstore = PermissionStore.get()

        if type(data) == list:
            for d in data:
                if type(d) == dict:
                    type_correct = True

                    perms = d.get('permissions')
                    invalid_perms.update(set(perms) - set(permstore.get_all_names()))

                    group_uri = d.get('group')
                    user_uri = d.get('user')

                    if group_uri:
                        try:
                            obj = res_groups.get_via_uri(group_uri)
                            self._objcache[group_uri] = obj
                        except NotFound:
                            invalid_groups.add(group_uri)

                    elif user_uri:
                        try:
                            obj = res_users.get_via_uri(user_uri)
                            self._objcache[user_uri] = obj
                        except NotFound:
                            invalid_users.add(user_uri)

                    else:
                        dct['missingPrincipal'] = 'No user or group provided.'

        if (dct or not type_correct
            or any([invalid_groups, invalid_perms, invalid_users])):
            if invalid_perms:
                dct.update({
                    'invalidPermissions': sorted(list(invalid_perms)),
                })
            if invalid_users:
                dct.update({
                    'invalidUsers': sorted(list(invalid_users)),
                })
            if invalid_groups:
                dct.update({
                    'invalidGroups': sorted(list(invalid_groups)),
                })
            content = self.resource._meta.serializer.to_json(dct)
            resp = HttpResponse(content, status=self.status_validation_error)
            raise ImmediateHttpResponse(response=resp)


class ResourceApidocView(ResourceView):
    must_authenticate = False

    def get_response(self, request, *args, **kwargs):
        api_name = getattr(self.resource, 'api_name', None) or kwargs.get('api_name')
        api = Api.get_api(api_name)

        schema = self.resource.build_schema()
        views = []
        for name, items in schema['views'].items():
            for view in items:
                views.append({
                    'view_name': name,
                    'method': view['method'],
                    'template_uri': view['urlPattern'],
                    'permission': view['permission'],
                })
        views = sorted(views, key=lambda d: (d['view_name'], d['method']))

        return render(request, 'apiapp/apidoc_resource_detail.html', {
            'api_name': api.api_name,
            'cur_page': self.resource._meta.resource_name,
            'resource_name': self.resource._meta.resource_name,
            'resource_obj': self.resource,
            'views': views,
        })


class ResourcePrivsView(ResourceView):
    methods = ['get', 'put']

    def get_response(self, request, *args, **kwargs):
        obj = self.get_object(request, *args, **kwargs)

        if request.method == 'PUT':
            return self.put(request, obj)

        return self.get(obj)

    def get(self, obj):
        perms_val = getattr(obj, 'zarafaApiPrivileges', None)

        privs = Privileges.parse(perms_val)
        lst = sorted(privs.perms)

        content = self.resource._meta.serializer.to_json(lst)
        return HttpResponse(content, mimetype=self.mimetype)

    def put(self, request, obj):
        data = json.loads(request.body)
        self.validate(data)

        obj.set_privs(data)
        obj.save()

        resp = self.get(obj)
        resp.status_code = self.status_accepted
        return resp

    def validate(self, data):
        permstore = PermissionStore.get()

        dct = {}
        type_correct = True
        if not type(data) == list:
            type_correct = False
            data = [data]

        invalids = set(data) - set(permstore.get_all_names())

        if not type_correct or invalids:
            if invalids:
                dct.update({
                    'invalidPermissions': sorted(list(invalids)),
                })
            content = self.resource._meta.serializer.to_json(dct)
            resp = HttpResponse(content, status=self.status_validation_error)
            raise ImmediateHttpResponse(response=resp)


class ResourceSchemaView(ResourceView):
    must_authenticate = False

    def get_response(self, request, *args, **kwargs):
        schema = self.resource.build_schema()
        return self.resource.create_response(request, schema)


class ResourceSoftDeleteView(ResourceView):
    methods = ['post']

    def get_response(self, request, *args, **kwargs):
        obj = self.get_object(request, *args, **kwargs)
        obj.soft_delete()
        return HttpResponse(status=self.status_accepted)


class ResourceSoftUndeleteView(ResourceView):
    methods = ['post']

    def get_response(self, request, *args, **kwargs):
        obj = self.get_object(request, *args, **kwargs)
        obj.soft_undelete()
        return HttpResponse(status=self.status_accepted)
