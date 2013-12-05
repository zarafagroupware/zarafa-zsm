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


from libzsm.rest_client.utils import get_api
from libzsm.rest_client.exc import Http403

from common import ApiTestBase


class AuthorizationTest(ApiTestBase):
    def __init__(self, *args, **kwargs):
        super(AuthorizationTest, self).__init__(*args, **kwargs)

        self.s = get_api()

    def setUp(self):
        ''' Trans [Harry (adm), Jeeves]        # NOQA
                                               # NOQA
                   |                           # NOQA
                   v                           # NOQA
                                               # NOQA
            Wheels [Rob]     ->  Cars [Jack]   # NOQA
                                               # NOQA
                   |                           # NOQA
                   v                           # NOQA
                                               # NOQA
            Bikes [Harry]                      # NOQA
                                               # NOQA
        Refer to the diagram:
            https://confluence.zarafa.com/pages/viewpage.action?pageId=20841313
        '''

        ## Hank is a tenant admin

        data = dict(
            name=u'trans',
        )
        self.ten_trans = self.s.create_tenant(initial=data)

        data = dict(
            username=u'hank',
            password=u'nk',
            name=u'Hank',
            surname=u'R',
            tenant=self.ten_trans,
            userServer=self.server1,
        )
        self.trans_hank = self.s.create_user(initial=data)

        data = {
            'permissions': [
                'ViewContact',
                'ViewGroup',
                'ViewGroupPrivileges',
                'ViewTenant',
                'ViewTenantAcl',
                'ViewUser',
                'ViewUserPrivileges',
                'WriteContact',
                'WriteGroup',
                'WriteGroupPrivileges',
                'WriteTenant',
                'WriteTenantAcl',
                'WriteUser',
                'WriteUserPrivileges',
            ],
            'user': self.trans_hank.resourceUri,
        }
        self.s.add_tenant_ace(self.ten_trans, data)

        data = [
            u'CreateTenant',
        ]
        self.s.put_user_privs(self.trans_hank, data)

        self.s_trans_hank = self.s.get_session(self.trans_hank)


        ## Jeeves is Hank's butler

        data = dict(
            username=u'jeeves',
            password=u'jv',
            name=u'Jeeves',
            surname=u'H',
            tenant=self.ten_trans,
            userServer=self.server1,
        )
        self.trans_jeeves = self.s_trans_hank.create_user(initial=data)

        self.s_trans_jeeves = self.s.get_session(self.trans_jeeves)


        ## Trans has a customer Wheels with a user Rob

        data = dict(
            name=u'wheels',
        )
        self.ten_wheels = self.s_trans_hank.create_tenant(initial=data)

        data = dict(
            username=u'rob',
            password=u'rb',
            name=u'Rob',
            surname=u'Dole',
            tenant=self.ten_wheels,
            userServer=self.server1,
        )
        self.wheels_rob = self.s_trans_hank.create_user(initial=data)

        data = [
            u'CreateTenant',
        ]
        self.s_trans_hank.put_user_privs(self.wheels_rob, data)

        self.s_wheels_rob = self.s.get_session(self.wheels_rob)


        ## Wheels has a customer Bikes with a user Harry

        data = dict(
            name=u'bikes',
        )
        self.ten_bikes = self.s_wheels_rob.create_tenant(initial=data)

        data = dict(
            username=u'harry',
            password=u'hr',
            name=u'Harry',
            surname=u'W',
            tenant=self.ten_bikes,
            userServer=self.server1,
        )
        self.bikes_harry = self.s_wheels_rob.create_user(initial=data)

        self.s_bikes_harry = self.s.get_session(self.bikes_harry)


        ## Wheels has a customer Cars with a user Jack

        data = dict(
            name=u'cars',
        )
        self.ten_cars = self.s_wheels_rob.create_tenant(initial=data)

        data = dict(
            username=u'jack',
            password=u'jk',
            name=u'Jack',
            surname=u'Hicks',
            tenant=self.ten_cars,
            userServer=self.server1,
        )
        self.cars_jack = self.s_wheels_rob.create_user(initial=data)

        self.s_cars_jack = self.s.get_session(self.cars_jack)


        ## Set some handy groupings

        self.all_tenants = [
            self.ten_trans,
            self.ten_wheels,
            self.ten_bikes,
            self.ten_cars,
        ]

    def tearDown(self):
        self.s_wheels_rob.delete_tenant(self.ten_bikes)
        self.s_wheels_rob.delete_tenant(self.ten_cars)
        self.s_trans_hank.delete_tenant(self.ten_wheels)
        self.s.delete_tenant(self.ten_trans)


    def test_neg_tenant_access(self):

        ## Hank only sees the tenants he created

        tens = self.s_trans_hank.all_tenant()
        self.assertEqual(2, len(tens), u'Incorrect number of tenants.')
        self.verify_iterable(tens, [self.ten_trans, self.ten_wheels])

        ## Jeeves sees no tenants

        tens = self.s_trans_jeeves.all_tenant()
        self.assertEqual(0, len(tens), u'Incorrect number of tenants.')

        ## Rob sees Bikes and Cars

        tens = self.s_wheels_rob.all_tenant()
        self.assertEqual(2, len(tens), u'Incorrect number of tenants.')
        self.verify_iterable(tens, [self.ten_bikes, self.ten_cars])

        ## Harry sees no tenants

        tens = self.s_bikes_harry.all_tenant()
        self.assertEqual(0, len(tens), u'Incorrect number of tenants.')

        ## Jack sees no tenants

        tens = self.s_cars_jack.all_tenant()
        self.assertEqual(0, len(tens), u'Incorrect number of tenants.')



        ## Hank can access Trans and Wheels, not Bikes or Cars

        self.s_trans_hank.get_tenant(id=self.ten_trans.id)
        self.s_trans_hank.get_tenant(id=self.ten_wheels.id)
        with self.assertRaises(Http403):
            self.s_trans_hank.get_tenant(id=self.ten_bikes.id)
        with self.assertRaises(Http403):
            self.s_trans_hank.get_tenant(id=self.ten_cars.id)

        ## Rob cannot access Trans nor Wheels, only Bikes and Cars

        with self.assertRaises(Http403):
            self.s_wheels_rob.get_tenant(id=self.ten_trans.id)
        with self.assertRaises(Http403):
            self.s_wheels_rob.get_tenant(id=self.ten_wheels.id)
        self.s_wheels_rob.get_tenant(id=self.ten_bikes.id)
        self.s_wheels_rob.get_tenant(id=self.ten_cars.id)

        ## Jeeves, Harry and Jack cannot access any tenants

        sessions = [
            self.s_trans_jeeves,
            self.s_bikes_harry,
            self.s_cars_jack,
        ]
        for session in sessions:
            for tenant in self.all_tenants:
                with self.assertRaises(Http403):
                    session.get_tenant(id=tenant.id)


    def test_neg_tenant_creation(self):

        ## Jeeves, Harry and Jack cannot create tenants

        sessions = [
            self.s_trans_jeeves,
            self.s_bikes_harry,
            self.s_cars_jack,
        ]

        for session in sessions:
            with self.assertRaises(Http403):
                data = dict(
                    name=u'dummy',
                )
                session.create_tenant(initial=data)


    def test_neg_user_access(self):

        ## Jeeves, Harry and Jack cannot access users on any tenant

        sessions = [
            self.s_trans_jeeves,
            self.s_bikes_harry,
            self.s_cars_jack,
        ]
        for session in sessions:
            for tenant in self.all_tenants:
                with self.assertRaises(Http403):
                    session.all_user(tenant=tenant)



        ## Jeeves, Harry and Jack cannot create users on any tenant

        sessions = [
            self.s_trans_jeeves,
            self.s_bikes_harry,
            self.s_cars_jack,
        ]
        for session in sessions:
            for tenant in self.all_tenants:
                with self.assertRaises(Http403):
                    data = dict(
                        username=u'dummy',
                        name=u'Dummy',
                        surname=u'H',
                        tenant=tenant,
                        userServer=self.server1,
                    )
                    session.create_user(initial=data)

        ## Rob cannot create users in Wheels

        with self.assertRaises(Http403):
            data = dict(
                username=u'dummy',
                name=u'Dummy',
                surname=u'H',
                tenant=self.ten_wheels,
                userServer=self.server1,
            )
            self.s_wheels_rob.create_user(initial=data)
