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


import functools
import re

from requests.auth import HTTPBasicAuth

from libzsm.uri import url_to_host
from libzsm.uri import url_to_path
from libzsm.uri import urlencode
from libzsm.uri import urljoin

from apirequest import ApiRequest
from exc import Http404
from exc import InvalidApiBaseUrl
from exc import InvalidView
from exc import MultipleObjectsReturned
from exc import ObjectDoesNotExist
from model import Model
from resource import Resource


class Api(object):
    rx_binop_method = re.compile('^([a-z]+)_([a-z]+)$')
    rx_ternop_method = re.compile('^([a-z]+)_([a-z]+)_([A-Za-z]+)$')

    def __init__(self, base_url, basic_auth=None):
        if basic_auth:
            assert len(basic_auth) == 2

        self.base_url = base_url
        self.basic_auth = basic_auth or tuple()

        self._resources = {}
        self._sitemap = {}

        self.last_apireq = None

    def __repr__(self):
        return "<{0}: {1}>".format(self.__class__.__name__, self.base_url)

    def __getattr__(self, key):
        # create_user(...) -> create(User, ...)
        # put_user_privs(...) -> subview_put('privs', ...)
        op_name, model_name, view_name = None, None, None

        # match either binary or ternary operation
        try:
            op_name, model_name, view_name = self.rx_ternop_method.findall(key)[0]
            op_name = 'subview_{0}'.format(op_name)
        except IndexError:
            try:
                op_name, model_name = self.rx_binop_method.findall(key)[0]
            except IndexError:
                raise AttributeError(key)

        # look up the method we're going to return
        op_method = getattr(self, op_name, None)
        if not op_method:
            raise AttributeError(key)

        # look up the resource
        resource = self.get_resource(model_name)
        if not resource:
            raise AttributeError(key)

        # return partial ternary method
        if view_name:
            if not resource.schema.views.get(view_name):
                raise AttributeError(key)

            op_method = functools.partial(op_method, view_name)

        # return partial binary method
        else:
            model_class = resource.model_class
            op_method = functools.partial(op_method, model_class)

        return op_method

    # Sessions

    def get_session(self, user):
        userid = u'{0}@{1}'.format(user.username, user.tenant.name)
        return self.__class__(
            self.base_url,
            basic_auth=(userid, user.password),
        )

    # Api requests

    def get_request_obj(self, path, data=None, method='get'):
        url = urljoin(self.base_url, path)

        auth = None
        if self.basic_auth:
            auth = HTTPBasicAuth(self.basic_auth[0], self.basic_auth[1])

        # cache this object for clients that need to introspect it
        self.last_apireq = ApiRequest(url, data, method, auth=auth)
        return self.last_apireq

    def call_api(self, path, data=None, method='get'):
        api_request = self.get_request_obj(path, data, method)
        return api_request.perform()

    # Resource initialization

    @property
    def sitemap(self):
        if not self._sitemap:
            try:
                self._sitemap = self.call_api(self.base_url)
                self._initialize_resources()
            except Http404:
                raise InvalidApiBaseUrl(self.base_url)
        return self._sitemap

    def _initialize_resources(self):
        def traverse(dct, parent=None):
            resources = {}

            for name, res in dct.items():
                host = url_to_host(self.base_url)
                apidoc_url = urljoin(host, res.get('apidoc'))
                schema_url = urljoin(host, res.get('schema'))

                resource = Resource(
                    self,
                    name,
                    res.get('relativePath'),
                    schema_url,
                    apidoc_url,
                    parent=parent,
                )
                self._resources[name] = resource
                resources[name] = resource

                child_resources = {}
                for att, val in res.items():
                    if att == 'children':
                        child_resources.update(
                            traverse(val, parent=resource)
                        )

                resource.children = child_resources

            return resources

        traverse(self.sitemap)

    @property
    def resources(self):
        if not self._resources:
            self._initialize_resources()
        return self._resources

    def get_resource(self, key):
        resource = None

        if isinstance(key, basestring):
            name = key
            resource = self.resources.get(name)
            if not resource:
                from libzsm import text
                name = text.make_plural(name)
                resource = self.resources.get(name)

        elif issubclass(key, Model):
            model_class = key
            for res in self.resources.values():
                if model_class == res.model_class:
                    resource = res

        return resource

    # Operations

    def get_list_uri(self, model_class, **kwargs):
        uri = None

        resource = self.get_resource(model_class)
        if resource.parent:
            param_name = resource.parent.singular_name
            parent_obj = kwargs.pop(param_name, None)
            if not parent_obj:
                raise Exception("Must provide kwarg '%s'" % param_name)
            uri = resource.get_list_uri(parent_obj)

        else:
            uri = resource.get_list_uri()

        return uri, kwargs

    # Operations: Reads

    def all(self, model_class, **kwargs):
        kwargs.update({
            'limit': 0,
        })
        return self.filter(model_class, **kwargs)

    def _filter_raw(self, model_class, **kwargs):
        uri, kwargs = self.get_list_uri(model_class, **kwargs)

        if kwargs:
            query = urlencode(kwargs)
            uri = '{0}?{1}'.format(uri, query)

        return self.call_api(uri)

    def filter(self, model_class, **kwargs):
        dct = self._filter_raw(model_class, **kwargs)
        objs = dct.get('objects')
        return [model_class.get_instance(_atts=obj) for obj in objs]

    def get(self, model_class, **kwargs):
        atts = {}

        # lookup by id
        id = kwargs.get('id')
        if id:
            uri, kwargs = self.get_list_uri(model_class, **kwargs)
            uri = urljoin(uri, id)

            atts = self.call_api(uri)

        # lookup by other params
        else:
            dct = self._filter_raw(model_class, **kwargs)
            objs = dct.get('objects')

            if not objs:
                raise ObjectDoesNotExist
            elif len(objs) > 1:
                raise MultipleObjectsReturned

            atts = objs[0]

        return model_class.get_instance(_atts=atts)

    # Operations: Writes

    def create(self, model_class, initial=None, **kwargs):
        # add parent obj value to kwargs
        resource = self.get_resource(model_class)
        if resource.parent:
            param_name = resource.parent.singular_name
            parent_obj = initial.get(param_name)
            if parent_obj:
                kwargs[param_name] = parent_obj

        uri, kwargs = self.get_list_uri(model_class, **kwargs)

        obj = resource.model_class.get_instance(initial=initial)

        dct = self.call_api(uri, data=obj.get_bound(), method='post')

        obj = resource.model_class.get_instance(_atts=dct)
        return obj

    def update(self, model_class, obj, **kwargs):
        self.call_api(obj.base_url, data=obj.get_bound(), method='put')

    def delete(self, model_class, obj, **kwargs):
        self.call_api(obj.base_url, method='delete')

        obj.bind_in_store('id', None)

    # Operations: Detail sub views

    def subview_get(self, view_name, obj, **kwargs):
        method = 'get'

        view = obj._resource.schema.views.get(view_name)
        if not view:
            raise InvalidView(view_name)
        url = urljoin(obj.base_url, view.get(method).relpath)

        return self.call_api(url, method=method)

    def subview_post(self, view_name, obj, data=None, **kwargs):
        method = 'post'

        view = obj._resource.schema.views.get(view_name)
        if not view:
            raise InvalidView(view_name)
        url = urljoin(obj.base_url, view.get(method).relpath)

        return self.call_api(url, data=data, method=method)

    def subview_put(self, view_name, obj, data, **kwargs):
        method = 'put'

        view = obj._resource.schema.views.get(view_name)
        if not view:
            raise InvalidView(view_name)
        url = urljoin(obj.base_url, view.get(method).relpath)

        return self.call_api(url, data=data, method=method)

    def add_tenant_ace(self, obj, data):
        resp = self.get_tenant_acl(obj)
        data = resp + [data]
        self.put_tenant_acl(obj, data)

    # Misc helpers

    def get_model_instance_by_path(self, path):
        '''Return a model instance from a path. This implementation is a
        bit clunky, as it relies on path comparisons and slicing.'''

        host = url_to_host(self.base_url)
        path = url_to_path(path)
        url = urljoin(host, path)

        # remove the base_path of the api
        path = re.sub('^{0}'.format(re.escape(self.base_url)), '', url)

        # in the remaining path, pattern match for the resource_name and id
        resource_name, id = re.findall('([^/]+)[/]([^/]+)[/]$', path)[0]

        resource = self.get_resource(resource_name)

        dct = self.call_api(url)
        obj = resource.model_class.get_instance(_atts=dct)

        return obj


if __name__ == '__main__':
    import sys
    sys.path.append('.')
    from utils import get_api

    import logging
    from logutils import get_logger

    if '-v' in sys.argv:
        logger = get_logger(__file__)
        logger.setLevel(logging.DEBUG)

    api = get_api()
    t1 = api.get_tenant(name="supertenant")
    print t1
    g1 = api.get_group(tenant=t1, name="admins")
    #print api.all_user(tenant=t1)
    #u1.description = u'a'
    #api.update_user(u1)
    #print api.create_user(initial={'name': 'h', 'surname': 'a', 'username': 'zz', 'tenant': t1})

    data = api.get_user_privs(g1)
    api.put_user_privs(g1, data=data)
    print data
