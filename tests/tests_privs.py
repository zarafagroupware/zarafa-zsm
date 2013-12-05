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


from libzsm.rest_client.exc import Http400
from libzsm.rest_client.exc import Http404

from common import ApiTestBase
from common import get_random_name


class PrivsTest(ApiTestBase):
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
            name=get_random_name(),
            members=[self.user1],
            tenant=self.tenant1,
        )
        self.group1 = self.api.create_group(initial=data)

    def tearDown(self):
        self.api.delete_tenant(self.tenant1)


    def set_verify_privs(self, obj, data):
        resp = self.api.subview_put('privs', obj, data)

        # check response against fixture
        self.assertEqual(202, self.api.last_apireq.response.status_code)
        self.assertEqual(data, resp)

        # fetch data again and make sure it matches the fixture
        resp2 = self.api.subview_get('privs', obj)

        self.assertEqual(200, self.api.last_apireq.response.status_code)
        self.assertEqual(data, resp2)

    def test_set_group_privs(self):
        data = [
            u'ViewGroup',
            u'WriteGroup',
        ]
        self.set_verify_privs(self.group1, data)

    def test_set_user_privs(self):
        data = [
            u'ViewUser',
            u'WriteUser',
        ]
        self.set_verify_privs(self.user1, data)


    def test_set_invalid_privs(self):
        data = [
            u'ViewTenant',
            u'WriteTenantz',
            u'ViewUserz',
        ]
        with self.assertRaises(Http400):
            self.api.put_user_privs(self.user1, data)

    def test_set_malformed_privs(self):
        data = u'ViewTenant'
        with self.assertRaises(Http400):
            self.api.put_user_privs(self.user1, data)


    def test_set_privs_invalid_resource(self):
        url = self.user1.base_url[:-2] + 'z/' + 'privileges/'
        data = [
            u'ViewTenant',
        ]

        apireq = self.api.get_request_obj(url, data=data, method='put')

        with self.assertRaises(Http404):
            apireq.perform()
