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


from datetime import timedelta

from libzsm.datehelper import utcnow
from libzsm.rest_client.exc import ObjectDoesNotExist

from common import ApiTestBase
from common import get_random_name


class UserTest(ApiTestBase):
    def setUp(self):
        data = dict(
            name=get_random_name(),
        )
        self.tenant1 = self.api.create_tenant(initial=data)

        data = dict(
            name=get_random_name(),
        )
        self.tenant2 = self.api.create_tenant(initial=data)

    def tearDown(self):
        self.api.delete_tenant(self.tenant1)
        self.api.delete_tenant(self.tenant2)


    def test_user_crud(self):
        data1 = dict(
            username=get_random_name(),
            name=u'Hank Wills',
            surname=u'Wills',
            tenant=self.tenant1,
            userServer=self.server1,
        )

        data2 = dict(
            username=get_random_name(),
            name=u'John Wayne',
            surname=u'Wayne',
            jpegPhoto=u'aGFuaw==',
            tenant=self.tenant2,
            userServer=self.server1,
        )

        # Pre-condition check
        with self.assertRaises(ObjectDoesNotExist):
            self.api.get_user(tenant=self.tenant1, username=data1['username'])
        with self.assertRaises(ObjectDoesNotExist):
            self.api.get_user(tenant=self.tenant2, username=data2['username'])

        # Create and verify
        user1 = self.api.create_user(initial=data1)
        self.verify_model_attributes(user1, data1)

        user2 = self.api.create_user(initial=data2)
        self.verify_model_attributes(user2, data2)

        # Fetch and verify
        user1 = self.api.get_user(tenant=self.tenant1, username=data1['username'])
        self.verify_model_attributes(user1, data1)

        user2 = self.api.get_user(tenant=self.tenant2, username=data2['username'])
        self.verify_model_attributes(user2, data2)

        # Update
        data1.update(dict(
            mail=u'will@yahoo.com',
            name=u'Willis Z',
            tenant=self.tenant1,
            userServer=self.server1,
            sendAsPrivilege=[
                user2,
            ],
        ))
        user1.update_with(data1)
        self.api.update_user(user1)

        data2.update(dict(
            mail=u'way@ibm.com',
            name=u'Wayne',
            jpegPhoto=None,
            tenant=self.tenant2,
            userServer=self.server1,
            sendAsPrivilege=[
                user1,
            ],
        ))
        user2.update_with(data2)
        self.api.update_user(user2)

        # Verify
        user1 = self.api.get_user(tenant=self.tenant1, username=data1['username'])
        self.verify_model_attributes(user1, data1)

        user2 = self.api.get_user(tenant=self.tenant2, username=data2['username'])
        self.verify_model_attributes(user2, data2)

        # Soft delete and verify
        self.api.post_user_softDelete(user1)
        user1 = self.api.get_user(tenant=self.tenant1, username=data1['username'])
        self.assertIsNotNone(user1.softDeletedDate)
        self.assertTrue(utcnow() - user1.softDeletedDate < timedelta(minutes=1),
                        u'softDeletedDate field is out of date.')

        # Soft undelete and verify
        self.api.post_user_softUndelete(user1)
        user1 = self.api.get_user(tenant=self.tenant1, username=data1['username'])
        self.assertIsNone(user1.softDeletedDate)

        # Delete
        self.api.delete_user(user1)
        self.api.delete_user(user2)

        # Post-condition check
        with self.assertRaises(ObjectDoesNotExist):
            self.api.get_user(tenant=self.tenant1, username=data1['username'])
        with self.assertRaises(ObjectDoesNotExist):
            self.api.get_user(tenant=self.tenant2, username=data2['username'])
