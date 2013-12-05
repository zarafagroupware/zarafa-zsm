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


from cmdline.libzsm.fixtures import registry

from common import ApiTestBase
from libzsm.fixture_loader.loader import FixtureLoader


class FixtureTest(ApiTestBase):
    def setUp(self):
        self.resources = ['servers', 'tenants', 'users', 'groups', 'contacts']
        self.store = registry.get_fixtures_mutated(*self.resources)
        self.loader = FixtureLoader(self.resources, self.store, api=self.api)
        self.loader.load()

    def tearDown(self):
        self.loader.unload()


    def update_mutate_verify(self, func):
        for name in self.resources:
            resource = self.api.resources.get(name)

            model_class = resource.model_class

            fixture = self.store[name][0]
            # don't mutate preloaded
            if getattr(fixture, '_is_preloaded', False):
                continue

            obj = self.loader.get_model_instance(fixture)

            # Update
            patch = func(resource, obj)

            obj.update_with(patch)
            self.api.update(model_class, obj)

            # Verify
            kwargs = {
                'id': obj.id,
            }
            if resource.parent:
                param_name = resource.parent.singular_name
                parent_obj = obj.get_parent_obj()
                kwargs.update({
                    param_name: parent_obj,
                })

            obj = self.api.get(model_class, **kwargs)
            self.verify_model_attributes(obj, patch)


    def unset_nullable(self, resource, obj):
        schema = resource.schema
        patch = {}
        for fname, field in schema.fields.items():
            if (field.nullable
                and not field.readonly
                and not fname in ['id']):
                if 'list' in field.signature:
                    patch[fname] = []
                else:
                    patch[fname] = None

        return patch

    def test_unset_nullable(self):
        self.update_mutate_verify(self.unset_nullable)
