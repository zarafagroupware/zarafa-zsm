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


from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.http import Http404

from tastypie.exceptions import BadRequest
from tastypie.utils import is_valid_jsonp_callback_value
from tastypie.utils import trailing_slash
from tastypie.utils.mime import build_content_type
from tastypie.utils.mime import determine_format
import tastypie.api

from apiapp.serializers import PrettyJSONSerializer


class Api(tastypie.api.Api):
    def register(self, resource, canonical=True):
        super(Api, self).register(resource, canonical=canonical)

        parent_resource_class = getattr(resource.__class__.Meta, 'parent_class', None)

        if parent_resource_class:
            parent_name = parent_resource_class.Meta.resource_name

            parent_resource = self._registry.get(parent_name)
            if not parent_resource:
                # Have to register the parent before children.
                raise ImproperlyConfigured("Uknown parent resource '%s'." % parent_name)

            # set the parent
            self.set_parent(resource._meta, parent_resource)
            self.set_parent(resource.__class__.Meta, parent_resource)

            # set the children
            self.set_child(parent_resource._meta, resource)
            self.set_child(parent_resource.__class__.Meta, resource)

    def set_child(self, target, child_resource):
        if not hasattr(target, 'children'):
            target.children = set()
        target.children.add(child_resource)

    def set_parent(self, target, parent_resource):
        target.parent = parent_resource

    @property
    def urls(self):
        pattern_list = [
            url(
                r"^(?P<api_name>%s)%s$" % (
                    self.api_name,
                    trailing_slash()
                ),
                self.wrap_view('top_level'),
                name="api_%s_top_level" % self.api_name
            ),
            url(
                r"^(?P<api_name>%s)/_schema/(?P<resource_name>\w+)%s$" % (
                    self.api_name,
                    trailing_slash()
                ),
                self.wrap_view('get_schema'),
                name="api_get_schema"
            ),
            url(
                r"^(?P<api_name>%s)/_apidoc/(?P<resource_name>\w+)%s$" % (
                    self.api_name,
                    trailing_slash()
                ),
                self.wrap_view('get_doc'),
                name="api_get_doc"
            ),
        ]

        for name, resource in sorted(self._registry.items()):
            if not getattr(resource, 'parent', None):
                self._registry[name].api_name = self.api_name
                pattern_list.append((r"^(?P<api_name>%s)/" % self.api_name, include(resource.urls)))

        urlpatterns = self.override_urls() + patterns(
            '', *pattern_list
        )
        return urlpatterns

    def top_level(self, request, api_name=None):
        serializer = PrettyJSONSerializer()
        available_resources = {}

        if api_name is None:
            api_name = self.api_name

        def render_resource(name, resource):
            dct = {
                'apidoc': self._build_reverse_url("api_get_doc", kwargs={
                    'api_name': api_name,
                    'resource_name': name,
                }),
                'relativePath': resource.get_relative_uri(),
                'schema': self._build_reverse_url("api_get_schema", kwargs={
                    'api_name': api_name,
                    'resource_name': name,
                }),
                'views': {}
            }

            for _, viewmeta in resource.viewregistry.get_all():
                view_name = viewmeta.name
                dct['views'][view_name] = viewmeta.get_template_uri(resource)

            if resource.children:
                dct['children'] = {}
                for child in resource.children:
                    n = child._meta.resource_name
                    dct['children'][n] = render_resource(n, child)

            return dct

        for name, resource in self._registry.items():
            if not resource.parent:
                available_resources[name] = render_resource(name, resource)

        desired_format = determine_format(request, serializer)
        options = {}

        if 'text/javascript' in desired_format:
            callback = request.GET.get('callback', 'callback')

            if not is_valid_jsonp_callback_value(callback):
                raise BadRequest('JSONP callback name is invalid.')

            options['callback'] = callback

        serialized = serializer.serialize(available_resources, desired_format, options)
        return HttpResponse(content=serialized, content_type=build_content_type(desired_format))

    def get_doc(self, request, **kwargs):
        from apiapp.resource_views import ResourceApidocView

        name = kwargs.get('resource_name')
        resource = self._registry.get(name)
        if not resource:
            raise Http404

        view = ResourceApidocView.as_view(resource=resource)
        view = resource.wrap_view(view)
        return view(request, **kwargs)

    def get_schema(self, request, **kwargs):
        from apiapp.resource_views import ResourceSchemaView

        name = kwargs.get('resource_name')
        resource = self._registry.get(name)
        if not resource:
            raise Http404

        view = ResourceSchemaView.as_view(resource=resource)
        view = resource.wrap_view(view)
        return view(request, **kwargs)

    @classmethod
    def get_api(cls, api_name):
        from apiapp import urls

        for name in dir(urls):
            obj = getattr(urls, name)
            if isinstance(obj, tastypie.api.Api):
                if getattr(obj, 'api_name', None) == api_name:
                    return obj

    def get_resource_names(self):
        names = sorted(self._registry.keys())
        return names
