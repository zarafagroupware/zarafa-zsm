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


import copy
import re

from django import template
from django.core.urlresolvers import reverse
from django.core.urlresolvers import Resolver404

from apiapp.django_ext.urlresolvers import cached_resolve

register = template.Library()


class ContextualNav(object):
    rx_view_type_pat = re.compile('api_dispatch_([0-9A-Za-z]+)_([0-9A-Za-z]+)')

    def __init__(self, context):
        self.context = context

        self.api = self.context.get('api')
        self.request = self.context.get('request')
        self.path = self.request.META.get('PATH_INFO')

        self.match = self.resolve_path(self.path)
        self.view_type, self.resource_name = self.find_view_type(self.match)

    @property
    def api_top_level_view_name(self):
        return 'api_%s_top_level' % self.api.api_name

    @property
    def api_top_level_view_uri(self):
        if not getattr(self, '_api_top_level_view_uri', None):
            uri = reverse(self.api_top_level_view_name,
                          kwargs={'api_name': self.api.api_name})
            self._api_top_level_view_uri = uri
        return self._api_top_level_view_uri

    def resolve_path(self, path):
        match = None
        try:
            match = cached_resolve(path)
        except Resolver404:
            pass
        return match

    def find_view_type(self, match):
        view_type, resource_name = None, None
        if match:
            try:
                pat = self.rx_view_type_pat
                view_type, resource_name = pat.findall(match.view_name)[0]
            except IndexError:
                pass
        return view_type, resource_name

    def add_resource(self, rev_breadcrumb, resource, kwargs):
        name = resource._meta.resource_name

        pk_key = resource.get_uri_pk_group_name()
        res_key = resource.get_uri_resource_group_name()

        pk = kwargs.get(pk_key)
        if pk:
            rev_breadcrumb.append({
                'title': pk,
                'url': reverse(resource.get_view_name_detail(), kwargs=kwargs),
            })
            kwargs.pop(pk_key)

        rev_breadcrumb.append({
            'title': name,
            'url': reverse(resource.get_view_name_list(), kwargs=kwargs),
        })
        kwargs.pop(res_key)

        return rev_breadcrumb, kwargs

    def get_breadcrumb(self):
        breadcrumb = [{
            'title': 'top level',
            'url': self.api_top_level_view_uri,
        }]

        rev_breadcrumb = []

        if self.resource_name:
            resource = self.api._registry[self.resource_name]

            kwargs = copy.copy(self.match.kwargs)

            # handle if it's a sub-view of the detail view
            viewmeta = resource.viewregistry.get(self.view_type)
            if viewmeta and getattr(viewmeta, 'is_detail_subview', False):
                head = re.sub('/$', '', self.path).split('/')[-1]
                rev_breadcrumb.append({
                    'title': head,
                    'url': self.path,
                })

            cur = resource
            rev_breadcrumb, kwargs = self.add_resource(rev_breadcrumb, cur, kwargs)

            while cur.parent:
                cur = cur.parent
                rev_breadcrumb, kwargs = self.add_resource(rev_breadcrumb, cur, kwargs)

        else:
            path = self.path

            path_parts = path.split('/')
            path_parts = [p for p in path_parts if p]
            top_level_parts = self.api_top_level_view_uri.split('/')
            top_level_parts = [p for p in top_level_parts if p]

            head = path_parts.pop()
            while len(path_parts) >= len(top_level_parts):
                if head:
                    rev_breadcrumb.append({
                        'title': head,
                        'url': path if path == self.path else '',
                    })

                head = path_parts.pop()
                path = '/'.join(path_parts) + '/'

        rev_breadcrumb.reverse()
        breadcrumb.extend(rev_breadcrumb)

        return breadcrumb

    def get_children(self):
        children = []

        if not self.resource_name:
            resources = [(n, r) for (n, r) in self.api._registry.items()
                         if not r.parent]
            resources.sort()

            for name, resource in resources:
                children.append({
                    'title': name,
                    'url': resource.get_relative_uri(),
                })

        elif self.view_type == 'detail':
            resource = self.api._registry[self.resource_name]

            for res in resource.children:
                name = res._meta.resource_name
                children.append({
                    'title': name,
                    'url': res.get_relative_uri(),
                })

            for _, viewmeta in resource.viewregistry.get_all():
                if getattr(viewmeta, 'is_detail_subview', False):
                    children.append({
                        'title': viewmeta.pretty_name,
                        'url': viewmeta.get_url_suffix(),
                    })

        children = sorted(children)

        return children

    def render(self):
        breadcrumb = self.get_breadcrumb()
        children = []
        links = []

        if (self.resource_name or
            (self.match and self.match.view_name == self.api_top_level_view_name)):
            children = self.get_children()

        if self.resource_name:
            links.extend([
                {
                    'title': 'apidoc',
                    'url': reverse('api_get_doc', kwargs={
                        'api_name': self.api.api_name,
                        'resource_name': self.resource_name,
                    }),
                },
                {
                    'title': 'schema',
                    'url': reverse('api_get_schema', kwargs={
                        'api_name': self.api.api_name,
                        'resource_name': self.resource_name,
                    }),
                },
            ])

        return {
            'breadcrumb': breadcrumb,
            'children': children,
            'links': links,
            'resource_name': self.resource_name,
        }


@register.inclusion_tag('apiapp/includes/api_debug_middlware_nav.html',
                        takes_context=True)
def render_debug_nav(context):
    nav = ContextualNav(context)
    return nav.render()
