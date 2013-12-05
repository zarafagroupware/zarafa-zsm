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

from django.core.exceptions import ValidationError

from pumpkin.filters import eq
from pumpkin.filters import opand

from tastypie.exceptions import NotFound as ResourceNotFound
from tastypie.exceptions import InvalidFilterError

from django_ext.urlresolvers import cached_resolve
from ldapdirectory import get_directory
from mapibackend.storebackend import StoreBackend
from models_ldap import User
from models_ldap import Tenant
from permissions import PermissionStore
from pumpkin_ext.directory import IntegrityError
from pumpkin_ext.filters import SearchParams
from resourcebase import ResourceBase
from schema import get_ldap_field_signature
from validation import LdapResourceValidation

logger = logging.getLogger(__name__)


class LdapResourceBase(ResourceBase):
    def __init__(self, *args, **kwargs):
        self._meta.validation = LdapResourceValidation(self)

        self.storebackend = StoreBackend()

        super(LdapResourceBase, self).__init__(*args, **kwargs)

    @property
    def directory(self):
        return get_directory()

    def get_model_field_name(self, api_field_name):
        field = self.fields[api_field_name]
        return field.attribute

    def get_model_field(self, api_field_name):
        model = self._meta.object_class
        name = self.get_model_field_name(api_field_name)
        return model._fields.get(name)

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)

    def get_field_signature(self, field_object):
        signature = super(LdapResourceBase, self).get_field_signature(field_object)

        if not signature:
            field_name = field_object.instance_name
            model_field = self.get_model_field(field_name)
            if model_field:
                signature = get_ldap_field_signature(model_field.__class__)

        return signature

    def build_filters(self, filters=None, request=None):
        basedn = None
        filter = None

        parts = []
        for arg_name, arg_value in filters.items():
            if arg_name in ['limit', 'offset']:  # XXX permit limit arg
                continue

            if arg_name not in self.fields or arg_name in ['limit']:
                raise InvalidFilterError("Not a valid filter: {0}".format(arg_name))

            if getattr(self.fields[arg_name], 'is_related', False):
                method = getattr(self, 'filter_on_{0}'.format(arg_name), None)
                if method:
                    basedn = method(arg_value)
                    continue
                else:
                    raise InvalidFilterError("Cannot filter on a relation field: {0}".format(arg_name))

            model_field_name = self.get_model_field_name(arg_name)
            part = eq(model_field_name, arg_value)
            parts.append(part)

        if parts:
            filter = opand(*parts)
        search_params = SearchParams(basedn=basedn, filter=filter)

        return search_params

    def get_object_list(self, request):
        object_list = []
        model = self._meta.object_class

        filters = request.GET.copy()
        search_params = self.build_filters(filters=filters, request=request)
        basedn = search_params.basedn

        # if we have a parent, fetch it and use the dn as basedn
        if self.parent:
            path = request.META.get('PATH_INFO')
            match = cached_resolve(path)
            group_name = self.parent.get_uri_pk_group_name()
            parent_pk = match.kwargs.get(group_name)

            parent_model = self.parent._meta.object_class
            parent_obj = parent_model.get_object('zarafaId', parent_pk)
            basedn = parent_obj.dn

        object_list = self.directory.search(
            model,
            basedn=basedn,
            search_filter=search_params.filter,
        )

        # restrict tenant list by ACL
        if object_list and isinstance(object_list[0], Tenant):
            object_list = [o for o in object_list
                           if request.user.has_perm('ViewTenant', o)]

        return object_list

    def obj_get(self, request=None, **kwargs):
        param_name = self.get_uri_pk_group_name()
        id = kwargs.get(param_name)
        model = self._meta.object_class

        try:
            object_list = self.directory.search(
                model,
                search_filter=eq(model.zarafaId, id)
            )
            return object_list[0]
        except IndexError:
            raise ResourceNotFound

    def obj_delete(self, request=None, **kwargs):
        model = self.obj_get(request, **kwargs)
        model.delete()

    # Data preparation.

    def full_dehydrate(self, bundle, skip_lazy_fields=False):
        # Dehydrate each field.
        for field_name, field_object in self.fields.items():
            # A touch leaky but it makes URI resolution work.
            if getattr(field_object, 'dehydrated_type', None) == 'related':
                field_object.api_name = self._meta.api_name
                field_object.resource_name = self._meta.resource_name

            if not skip_lazy_fields or not getattr(field_object, 'lazy', False):
                bundle.data[field_name] = field_object.dehydrate(bundle)

                # Check for an optional method to do further dehydration.
                method = getattr(self, "dehydrate_%s" % field_name, None)

                if method:
                    bundle.data[field_name] = method(bundle)

        bundle = self.dehydrate(bundle)
        return bundle

    def full_hydrate(self, bundle):
        '''We need to overload this to set m2m fields as well.'''
        if bundle.obj is None:
            bundle.obj = self._meta.object_class()

        bundle = self.hydrate(bundle)

        for field_name, field_object in self.fields.items():
            if field_object.readonly is True:
                continue

            # NOTE: special case m2m fields
            if getattr(field_object, 'is_m2m', False):
                lst = field_object.hydrate_m2m(bundle)
                model_field_name = self.get_model_field_name(field_name)
                setattr(bundle.obj, model_field_name, [e.obj for e in lst])
                continue

            # Check for an optional method to do further hydration.
            method = getattr(self, "hydrate_%s" % field_name, None)

            if method:
                bundle = method(bundle)

            if field_object.attribute:
                value = field_object.hydrate(bundle)

                if value is not None or field_object.null:
                    # We need to avoid populating M2M data here as that will
                    # cause things to blow up.
                    if not getattr(field_object, 'is_related', False):
                        setattr(bundle.obj, field_object.attribute, value)
                    elif not getattr(field_object, 'is_m2m', False):
                        if value is not None:
                            setattr(bundle.obj, field_object.attribute, value.obj)
                        elif field_object.blank:
                            continue
                        elif field_object.null:
                            setattr(bundle.obj, field_object.attribute, value)

        return bundle

    def hydrate(self, bundle):
        obj = bundle.obj

        # build a dict from bundle.data by resolving resource names
        # to model names
        model_data = {}
        for fname, f in self.fields.items():
            model_att_name = f.attribute
            val = bundle.data.get(fname)
            if val:
                model_data[model_att_name] = val

        # make sure the fields that make up Model._rdn_ are set
        for fname, f in obj._fields.items():
            if fname in obj.get_mandatory_fields():
                val = model_data.get(fname)
                if val:
                    setattr(obj, fname, val)

        return bundle

    def obj_create(self, bundle, request=None, **kwargs):
        try:
            bundle = self.full_hydrate(bundle)
        except ResourceNotFound as e:
            raise ValidationError(e.message)

        # Set ACL
        if isinstance(bundle.obj, Tenant) and hasattr(request, 'user'):
            perm_names = PermissionStore.get().get_all_names(is_acl=True)
            bundle.obj.set_acl(perm_names, user=request.user)

        try:
            bundle.obj.save()
        except IntegrityError:
            raise ValidationError(u'Already exists')

        # NOTE: perform sync zarafa <-> ldap
        if isinstance(bundle.obj, User):
            self.storebackend.sync_users()

        return bundle

    def obj_update(self, bundle, request=None, **kwargs):
        # Fetch object, then hydrate and save
        object_list = self.directory.search(
            bundle.obj.__class__,
            search_filter=eq('zarafaId', bundle.data['id']),
        )
        bundle.obj = object_list[0]

        try:
            bundle = self.full_hydrate(bundle)
        except ResourceNotFound as e:
            raise ValidationError(e.message)

        bundle.obj.save()

        return bundle

    # Views.

    def get_list(self, request, **kwargs):
        objects = self.obj_get_list(request=request, **self.remove_api_resource_names(kwargs))
        sorted_objects = self.apply_sorting(objects, options=request.GET)

        paginator = self._meta.paginator_class(request.GET, sorted_objects, resource_uri=self.get_resource_list_uri(), limit=self._meta.limit)
        to_be_serialized = paginator.page()

        # Dehydrate the bundles in preparation for serialization.
        bundles = [self.build_bundle(obj=obj, request=request) for obj in to_be_serialized['objects']]
        to_be_serialized['objects'] = [self.full_dehydrate(bundle, skip_lazy_fields=True)
                                       for bundle in bundles]
        to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
        return self.create_response(request, to_be_serialized)
