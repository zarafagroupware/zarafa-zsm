# -*- coding: utf-8 -*-
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
from common import ApiTestBase
from common import get_random_name


class SimpleValidationTest(ApiTestBase):
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

    def tearDown(self):
        self.api.delete_tenant(self.tenant1)


    def test_invalid_field(self):
        data = dict(
            mooCompanyServer='server-best',
        )

        url = self.tenant1.base_url
        with self.assertRaises(Http400):
            self.api.call_api(url, data=data, method='patch')

    def test_invalid_binary(self):
        data = dict(
            jpegPhoto=u'é',
        )

        url = self.user1.base_url
        with self.assertRaises(Http400):
            self.api.call_api(url, data=data, method='patch')

    def test_invalid_bool(self):
        data = dict(
            isAccount=u'a',
        )

        url = self.tenant1.base_url
        with self.assertRaises(Http400):
            self.api.call_api(url, data=data, method='patch')

    def test_invalid_int(self):
        data = dict(
            userDefaultQuotaHard=u'a',
        )

        url = self.tenant1.base_url
        with self.assertRaises(Http400):
            self.api.call_api(url, data=data, method='patch')

    def test_invalid_unicode(self):
        data = dict(
            name=1,
        )

        url = self.tenant1.base_url
        with self.assertRaises(Http400):
            self.api.call_api(url, data=data, method='patch')

    def test_invalid_unicode_list(self):
        data = dict(
            mailDomains=[u'ok', 1],
        )

        url = self.tenant1.base_url
        with self.assertRaises(Http400):
            self.api.call_api(url, data=data, method='patch')


class RelationalValidationTest(ApiTestBase):
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

    def tearDown(self):
        # cascade deletes the user as well
        self.api.delete_tenant(self.tenant1)


    def test_invalid_relation(self):
        data = dict(
            systemAdmin=self.user1.base_url + 'a',
        )

        self.tenant1.update_with(data)

        url = self.tenant1.base_url
        apireq = self.api.get_request_obj(url, data=data, method='patch')
        with self.assertRaises(Http400):
            apireq.perform()
