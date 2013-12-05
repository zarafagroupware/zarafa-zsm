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


from django.conf import settings
from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.core.exceptions import ValidationError
from django.core.urlresolvers import NoReverseMatch
from django.core.urlresolvers import reverse
from django.utils.cache import patch_cache_control
from django.views.decorators.csrf import csrf_exempt

from tastypie import fields
from tastypie import http
from tastypie.authentication import BasicAuthentication
from tastypie.authentication import Authentication  # NOQA
from tastypie.authorization import Authorization  # NOQA
from tastypie.bundle import Bundle
from tastypie.exceptions import BadRequest
import tastypie.resources

from libzsm.fixture_builder.base import Reference
from libzsm.fixtures import registry

from authentication import LdapAuthenticationBackend
from authorization import LdapAuthorization
from models_ldap import Group
from models_ldap import Tenant
from models_ldap import User
from permissions import PermissionStore
from resource_viewmetas import ResourceAclViewMeta
from resource_viewmetas import ResourceDetailViewMeta
from resource_viewmetas import ResourceListViewMeta
from resource_viewmetas import ResourcePrivsViewMeta
from resource_viewmetas import ResourceSoftDeleteViewMeta
from resource_viewmetas import ResourceSoftUndeleteViewMeta
from schema import get_resource_detail_uri
from serializers import PrettyJSONSerializer
from viewregistry.registry import ViewRegistry


class ResourceBase(tastypie.resources.Resource):
    def __init__(self, *args, **kwargs):
        # Configure Meta
        self._meta.always_return_data = True
        self._meta.authentication = BasicAuthentication(
            backend=LdapAuthenticationBackend(),
            realm='zsm')  # just use one realm for now
            #realm=self._meta.resource_name)
        self._meta.authorization = LdapAuthorization(self)

        #self._meta.authentication = Authentication()
        #self._meta.authorization = Authorization()

        self._meta.serializer = PrettyJSONSerializer()

        # Init fixture data for use in schema
        self.fixture_data = registry.get_single_fixture(self._meta.resource_name)

        # Register all the views
        self.viewregistry = ViewRegistry()

        self.viewregistry.register(ResourceDetailViewMeta())
        self.viewregistry.register(ResourceListViewMeta())

        if self._meta.object_class in [Tenant]:
            self.viewregistry.register(ResourceAclViewMeta())

        if self._meta.object_class in [Group, User]:
            self.viewregistry.register(ResourcePrivsViewMeta())

        if self._meta.object_class in [User]:
            self.viewregistry.register(ResourceSoftDeleteViewMeta())
            self.viewregistry.register(ResourceSoftUndeleteViewMeta())

        super(ResourceBase, self).__init__(*args, **kwargs)

    # Hierarchical relationships

    @property
    def children(self):
        return getattr(self._meta, 'children', [])

    @property
    def parent(self):
        return getattr(self._meta, 'parent', None)

    # Url pattern stuff that needs to be specialized per class

    def get_uri_pk_regex(self):
        return '\w[\w-]*'

    def get_uri_pk_group_name(self):
        return '{0}_pk'.format(self._meta.resource_name)

    def get_uri_resource_group_name(self):
        return 'resource_{0}'.format(self._meta.resource_name)

    def get_view_name(self, view_name):
        return 'api_dispatch_{0}_{1}'.format(view_name, self._meta.resource_name)

    def get_view_name_list(self):
        return 'api_dispatch_list_{0}'.format(self._meta.resource_name)

    def get_view_name_detail(self):
        return 'api_dispatch_detail_{0}'.format(self._meta.resource_name)

    def get_relative_uri(self):
        # NOTE: Not using the url patterns
        return '{0}/'.format(self._meta.resource_name)

    # Urls

    def get_detail_uri_prefix(self):
        detail_uri_prefix = r"^(?P<%s>%s)/(?P<%s>%s)" % (
            self.get_uri_resource_group_name(),
            self._meta.resource_name,
            self.get_uri_pk_group_name(),
            self.get_uri_pk_regex(),
        )
        return detail_uri_prefix

    def base_urls(self):
        urls = []

        # Include urls from view registry
        for view_name, viewmeta in self.viewregistry.get_all():
            urls.append(viewmeta.get_url(self))

        # Include child urls
        child_urls = []
        for child in self.children:
            child_urls.extend(child.urls)

        detail_uri_prefix = self.get_detail_uri_prefix()
        if child_urls:
            child_pat = url(detail_uri_prefix + '/', include(patterns('', *child_urls)))
            urls.append(child_pat)

        return urls

    def get_detail_view_kwargs(self, obj=None):
        '''Build a dict with all the kwargs needed to reverse the
        detail view.'''
        kwargs = {
            self.get_uri_pk_group_name(): obj and obj.zarafaId,
            self.get_uri_resource_group_name(): self._meta.resource_name,
        }

        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        # MRO like thing where we visit all the parents recursively
        cur = self
        while cur.parent:
            cur_parent = obj and cur.get_parent(obj)

            kwargs.update({
                cur.parent.get_uri_pk_group_name(): cur_parent and cur_parent.zarafaId,
                cur.parent.get_uri_resource_group_name(): cur.parent._meta.resource_name,
            })

            cur = cur.parent

        return kwargs

    def get_list_view_kwargs(self, obj=None):
        kwargs = self.get_detail_view_kwargs()

        # remove pk key for the current resource
        key = '{0}_pk'.format(self._meta.resource_name)
        kwargs.pop(key, None)

        return kwargs

    def get_resource_uri(self, bundle_or_obj):
        obj = bundle_or_obj.obj if isinstance(bundle_or_obj, Bundle) else bundle_or_obj

        view_name = self.get_view_name_detail()
        kwargs = self.get_detail_view_kwargs(obj)

        return reverse(view_name, kwargs=kwargs)

    def get_resource_list_uri(self):
        kwargs = {
            self.get_uri_resource_group_name(): self._meta.resource_name,
        }

        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        try:
            view_name = self.get_view_name_list()
            return self._build_reverse_url(view_name, kwargs=kwargs)
        except NoReverseMatch:
            return None

    # Schema

    def get_field_signature(self, field_object):
        if field_object.instance_name == 'resource_uri':
            related_resource_name = self._meta.resource_name
            return u'single of {0}'.format(related_resource_name)

        if getattr(field_object, 'is_related', False):
            related_resource_name = field_object.to_class._meta.resource_name
            if getattr(field_object, 'is_m2m', False):
                signature = u'list of {0}'.format(related_resource_name)
            else:
                signature = u'single of {0}'.format(related_resource_name)
            return signature

    def build_schema(self):
        data = {
            'fields': {},
            'default_limit': self._meta.limit,
            'views': [],
        }

        # Add view information
        views = {}
        store = PermissionStore.get()
        for perm in store.get_all():
            if perm.resource == self:
                dct = dict(
                    method=perm.method,
                    permission=perm.name,
                    urlPattern=perm.urlpat,
                )

                viewmeta = self.viewregistry.get(perm.view_type)
                relative_path = getattr(viewmeta, 'get_url_suffix', lambda: None)()
                if relative_path:
                    dct['detailRelativePath'] = relative_path

                views.setdefault(perm.view_type, []).append(dct)

        f = lambda d: d['method']
        views = dict([(k, sorted(v, key=f)) for (k, v) in views.items()])

        data['views'] = views

        if self._meta.ordering:
            data['ordering'] = self._meta.ordering

        if self._meta.filtering:
            data['filtering'] = self._meta.filtering

        # build embellished dict per field
        for field_name, field_object in self.fields.items():
            example = getattr(self.fixture_data, field_name, None)
            if isinstance(example, Reference):
                example = str(example)
            help_text = field_object.help_text
            lazy = getattr(field_object, 'lazy', False)
            signature = self.get_field_signature(field_object)
            type = field_object.dehydrated_type

            if not signature:
                signature = type

            if field_name == 'resource_uri':
                help_text = 'The url that uniquely identifies this resource.'

            data['fields'][field_name] = {
                'blank': field_object.blank,
                'default': field_object.default,
                'example': example,
                'help_text': help_text,
                'lazy': lazy,
                'nullable': field_object.null,
                'readonly': field_object.readonly,
                'signature': signature,
                'type': type,
                'unique': field_object.unique,
            }

        # set up inter-field dependencies
        for field_name, field_object in self.fields.items():
            example = data['fields'][field_name]['example']
            type = data['fields'][field_name]['type']

            if field_name == 'resource_uri':
                id = data['fields'].get('id', {}).get('example', '')
                example = get_resource_detail_uri(self, id)

            elif type == 'related':
                cls = field_object.to_class
                if getattr(field_object, 'is_m2m', False):
                    example = example or []
                    example = [get_resource_detail_uri(cls(), e.pk) for e in example]
                else:
                    example = get_resource_detail_uri(cls(), example)

            data['fields'][field_name]['example'] = example

        return data

    # Views

    def wrap_view(self, view):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            try:
                callback = view
                if isinstance(view, basestring):
                    callback = getattr(self, view)
                response = callback(request, *args, **kwargs)


                if request.is_ajax():
                    # IE excessively caches XMLHttpRequests, so we're disabling
                    # the browser cache here.
                    # See http://www.enhanceie.com/ie/bugs.asp for details.
                    patch_cache_control(response, no_cache=True)

                return response
            except (BadRequest, fields.ApiFieldError), e:
                return http.HttpBadRequest(e.args[0])
            except ValidationError, e:
                if e.messages:
                    dct = dict(errors=e.messages)
                    format = self.determine_format(request)
                    return http.HttpBadRequest(self.serialize(request, dct, format), mimetype=format)
                return http.HttpBadRequest()
            except Exception, e:
                if hasattr(e, 'response'):
                    return e.response

                # A real, non-expected exception.
                # Handle the case where the full traceback is more helpful
                # than the serialized error.
                if settings.DEBUG and getattr(settings, 'TASTYPIE_FULL_DEBUG', False):
                    raise

                # Rather than re-raising, we're going to things similar to
                # what Django does. The difference is returning a serialized
                # error message.
                return self._handle_500(request, e)

        return wrapper
