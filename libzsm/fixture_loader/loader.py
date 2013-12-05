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


from collections import namedtuple
import sys

from libzsm.fixture_builder.base import Reference
from libzsm.rest_client.utils import get_api


class PkStore(object):
    def __init__(self):
        self.store = {}

        self.item_type = namedtuple('PkTuple', 'pk resource_obj')

    def set(self, ref, resource_obj, pk):
        self.store[ref] = self.item_type(resource_obj=resource_obj, pk=pk)

    def get(self, ref):
        return self.store.get(ref)


class FixtureLoader(object):
    def __init__(self, ordered_resources, fixture_store, pk_name='id', api=None):
        self.ordered_resources = ordered_resources
        self.fixture_store = fixture_store
        self.pk_name = pk_name
        self.api = api

        if not self.api:
            self.api = get_api()

        self.pk_store = PkStore()

    def load(self):
        # pass 1 - insert incomplete
        # pass 2 - fill in references
        for phase in ['create', 'update']:
            for resource_name in self.ordered_resources:
                fixtures = self.fixture_store[resource_name]
                for fixture in fixtures:
                    self.load_fixture(resource_name, fixture, phase=phase)

    def unload(self):
        for resource_name in self.ordered_resources:
            fixtures = self.fixture_store[resource_name]
            for fixture in fixtures:
                self.unload_fixture(resource_name, fixture)

    def eval_field(self, fname, value):
        if type(value) == list:
            value = [self.eval_field(fname, v) for v in value]
            value = [v for v in value if v is not None]

        if isinstance(value, Reference):
            pktuple = self.pk_store.get(value)
            if pktuple:
                # if this is the pk field then we need the verbatim value,
                # otherwise eval to an implementation specific value
                if fname == self.pk_name:
                    value = pktuple.pk
                else:
                    value = self.eval_field_ref(pktuple)
            else:
                value = None

        return value

    def eval_field_ref(self, pktuple):
        obj = pktuple.resource_obj
        return obj

    def pprint_initial(self, phase, resource_name, fixture, initial):
        # keep quiet when running under test
        if 'nose' in ' '.join(sys.argv):
            return

        fix_name = fixture.__name__

        ss = [u'==== Phase: {0}, Resource: {1}, Fixture: {2} ===='
              .format(phase.upper(), resource_name, fix_name)]
        fmt = u'{0:40} {1}'

        for key, value in sorted(initial.items()):
            s = fmt.format(repr(key), repr(value))
            ss.append(s)

        s = u'\n'.join(ss)
        print(s)

    def load_fixture(self, resource_name, fixture, phase='create'):
        initial = {}
        pk_key_value = getattr(fixture, self.pk_name)

        for fname, value in fixture._fields.items():
            value = self.eval_field(fname, value)
            if value is not None:
                initial[fname] = value

        resource = self.api.get_resource(resource_name)
        model_class = resource.model_class

        if phase == 'create':
            self.pprint_initial(phase, resource_name, fixture, initial)

            if getattr(fixture, '_is_preloaded', False):
                obj = self.api.get(model_class, name=fixture.name)
            else:
                obj = self.api.create(model_class, initial=initial)

            pk_val = getattr(obj, self.pk_name)
            self.pk_store.set(pk_key_value, obj, pk_val)

        else:
            self.pprint_initial(phase, resource_name, fixture, initial)
            pk_val = initial.get(self.pk_name)

            kwargs = {
                self.pk_name: pk_val,
            }
            if resource.parent:
                param_name = resource.parent.singular_name
                parent_obj = initial.get(param_name)
                kwargs.update({
                    param_name: parent_obj,
                })

            obj = self.api.get(model_class, **kwargs)
            obj.update_with(initial)
            self.api.update(model_class, obj)

    def unload_fixture(self, resource_name, fixture):
        # we only need to delete tenants
        if resource_name in ['tenants']:
            pk_ref = getattr(fixture, self.pk_name)
            pktuple = self.pk_store.get(pk_ref)

            obj = pktuple.resource_obj
            model_class = obj.__class__

            self.api.delete(model_class, obj)

    def get_model_instance(self, fixture):
        ref = getattr(fixture, self.pk_name)
        pktuple = self.pk_store.get(ref)
        obj = pktuple.resource_obj
        return obj
