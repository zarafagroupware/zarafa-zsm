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


from libzsm.rest_client.exc import ObjectDoesNotExist
from common import ApiTestBase
from common import get_random_name


class GroupTest(ApiTestBase):
    def setUp(self):
        data = dict(
            name=get_random_name(),
        )
        self.tenant1 = self.api.create_tenant(initial=data)

        data = dict(
            username=get_random_name(),
            name=get_random_name(),
            surname=get_random_name(),
            tenant=self.tenant1,
            userServer=self.server1,
        )
        self.user1 = self.api.create_user(initial=data)

        data = dict(
            username=get_random_name(),
            name=get_random_name(),
            surname=get_random_name(),
            tenant=self.tenant1,
            userServer=self.server1,
        )
        self.user2 = self.api.create_user(initial=data)

    def tearDown(self):
        self.api.delete_tenant(self.tenant1)


    def test_group_crud(self):
        data1 = dict(
            name=get_random_name(),
            mail=u'g1@enterprise.com',
            members=[
                self.user1,
                self.user2,
            ],
            sendAsPrivilege=[
            ],
            tenant=self.tenant1,
        )

        data2 = dict(
            name=get_random_name(),
            mail=u'g2@enterprise.com',
            members=[],
            sendAsPrivilege=[
                self.user1,
                self.user2,
            ],
            tenant=self.tenant1,
        )

        # Pre-condition check
        with self.assertRaises(ObjectDoesNotExist):
            self.api.get_group(tenant=self.tenant1, name=data1['name'])
        with self.assertRaises(ObjectDoesNotExist):
            self.api.get_group(tenant=self.tenant1, name=data2['name'])

        # Create and verify
        group1 = self.api.create_group(initial=data1)
        self.verify_model_attributes(group1, data1)

        group2 = self.api.create_group(initial=data2)
        self.verify_model_attributes(group2, data2)

        # Fetch and verify
        group1 = self.api.get_group(tenant=self.tenant1, name=data1['name'])
        self.verify_model_attributes(group1, data1)

        group2 = self.api.get_group(tenant=self.tenant1, name=data2['name'])
        self.verify_model_attributes(group2, data2)

        # Update
        data1.update(dict(
            mail=u'g2@enterprise.com',
            members=[
            ],
            sendAsPrivilege=[
                self.user2,
            ],
        ))
        group1.update_with(data1)
        self.api.update_group(group1)

        data2.update(dict(
            mail=u'g2@enterprise.com',
            members=[
                self.user1,
                self.user2,
            ],
            sendAsPrivilege=[
                self.user1,
            ],
        ))
        group2.update_with(data2)
        self.api.update_group(group2)

        # Verify
        group1 = self.api.get_group(tenant=self.tenant1, name=data1['name'])
        self.verify_model_attributes(group1, data1)

        group2 = self.api.get_group(tenant=self.tenant1, name=data2['name'])
        self.verify_model_attributes(group2, data2)

        # Delete
        self.api.delete_group(group1)
        self.api.delete_group(group2)

        # Post-condition check
        with self.assertRaises(ObjectDoesNotExist):
            self.api.get_group(tenant=self.tenant1, name=data1['name'])
        with self.assertRaises(ObjectDoesNotExist):
            self.api.get_group(tenant=self.tenant1, name=data2['name'])
