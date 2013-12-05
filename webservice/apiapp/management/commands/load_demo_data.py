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


import logging

from django.core.management.base import BaseCommand

from libzsm.rest_client.logutils import get_logger
from libzsm.rest_client.utils import get_api

from conf.settings import config


class Command(BaseCommand):
    help = "Load demo data into ldap."

    def handle(self, *args, **options):
        # a bit hacky, set the logger level if we have -v
        if int(options.get('verbosity')) > 1:
            logger = get_logger(__file__)
            logger.setLevel(logging.DEBUG)

        self.load()

    @property
    def s(self):
        if not getattr(self, '_s', None):
            self._s = get_api()
        return self._s

    @property
    def server1(self):
        if not getattr(self, '_server1', None):
            self._server1 = self.s.get_server(name=config.ZARAFA_SERVER1_NAME)
        return self._server1


    def load(self):

        ##############################################################
        ## Cloudy
        ##############################################################

        # admin@origin creates tenant cloudy.com
        data = dict(
            name=u'cloudy.com',
            mailDomains=[
                u'cloudy.com',
            ],
        )
        self.ten_cloudy = self.s.create_tenant(initial=data)


        # admin@origin creates user clark@cloudy.com
        data = dict(
            username=u'clark',
            name=u'Clark',
            password=u'c',
            surname=u'C',
            mail=u'clark@cloudy.com',
            aliases=[
                u'c@cloudy.com',
            ],
            tenant=self.ten_cloudy,
            userServer=self.server1,
        )
        self.cloudy_clark = self.s.create_user(initial=data)

        # get a session for clark@cloudy.com
        self.s_cloudy_clark = self.s.get_session(self.cloudy_clark)

        # admin@origin grants ace on cloudy.com to clark@cloudy.com
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
            'user': self.cloudy_clark.resourceUri,
        }
        self.s.add_tenant_ace(self.ten_cloudy, data)



        # clark@cloudy.com creates user colin@cloudy.com
        data = dict(
            username=u'colin',
            name=u'Colin',
            password=u'c',
            surname=u'C',
            mail=u'colin@cloudy.com',
            tenant=self.ten_cloudy,
            userServer=self.server1,
        )
        self.cloudy_colin = self.s_cloudy_clark.create_user(initial=data)

        # get a session for colin@cloudy.com
        self.s_cloudy_colin = self.s.get_session(self.cloudy_colin)

        # clark@cloudy.com creates group admins@cloudy.com
        data = dict(
            name=u'admins',
            tenant=self.ten_cloudy,
            members=[
                self.cloudy_clark,
                self.cloudy_colin,
            ],
        )
        self.cloudy_admins = self.s_cloudy_clark.create_group(initial=data)

        # clark@cloudy.com grants privs to admins@cloudy.com
        data = [
            'CreateTenant',
        ]
        self.s_cloudy_clark.put_group_privs(self.cloudy_admins, data)


        ##############################################################
        ## Pianos
        ##############################################################

        # colin@cloudy.com creates tenant pianos.com
        data = dict(
            name=u'pianos.com',
            mailDomains=[
                u'pianos.com',
            ],
        )
        self.ten_pianos = self.s_cloudy_colin.create_tenant(initial=data)

        # colin@cloudy.com grants ace on pianos.com to admins@cloudy.com
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
            'group': self.cloudy_admins.resourceUri,
        }
        self.s_cloudy_colin.add_tenant_ace(self.ten_pianos, data)

        # clark@cloudy.com creates user pete@pianos.com
        data = dict(
            username=u'pete',
            name=u'Pete',
            password=u'p',
            surname=u'P',
            mail=u'pete@pianos.com',
            tenant=self.ten_pianos,
            userServer=self.server1,
        )
        self.pianos_pete = self.s_cloudy_clark.create_user(initial=data)


        ##############################################################
        ## Transit
        ##############################################################

        # clark@cloudy.com creates tenant transit.com
        data = dict(
            name=u'transit.com',
            mailDomains=[
                u'transit.com',
            ],
        )
        self.ten_transit = self.s_cloudy_clark.create_tenant(initial=data)

        # clark@cloudy.com creates a user todd@transit.com
        data = dict(
            username=u'todd',
            name=u'Todd',
            password=u't',
            surname=u'T',
            mail=u'todd@transit.com',
            aliases=[
                u't@transit.com',
            ],
            tenant=self.ten_transit,
            userServer=self.server1,
        )
        self.transit_todd = self.s_cloudy_clark.create_user(initial=data)

        # get a session for todd@transit.com
        self.s_transit_todd = self.s.get_session(self.transit_todd)

        # clark@cloudy.com grants privs to todd@transit.com
        data = [
            'CreateTenant',
        ]
        self.s_cloudy_clark.put_user_privs(self.transit_todd, data)

        # clark@cloudy.com grants ace on transit.com to todd@transit.com
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
            'user': self.transit_todd.resourceUri,
        }
        self.s_cloudy_clark.add_tenant_ace(self.ten_transit, data)


        ##############################################################
        ## Bikes
        ##############################################################

        # todd@transit.com creates tenant bikes.com
        data = dict(
            name=u'bikes.com',
            mailDomains=[
                u'bikes.com',
            ],
        )
        self.ten_bikes = self.s_transit_todd.create_tenant(initial=data)

        # todd@transit.com sets email domains for bikes.com
        self.ten_bikes.mailDomains.extend([
            u'bikes.com',
            u'fietsen.nl',
        ])
        self.s_transit_todd.update_tenant(self.ten_bikes)

        # todd@transit.com creates user bob@bikes.com
        data = dict(
            username=u'bob',
            name=u'Bob',
            password=u'b',
            surname=u'B',
            mail=u'bob@bikes.com',
            tenant=self.ten_bikes,
            userServer=self.server1,
        )
        self.bikes_bob = self.s_transit_todd.create_user(initial=data)


        ##############################################################
        ## Railroads
        ##############################################################

        # todd@transit.com creates tenant railroads.com
        data = dict(
            name=u'railroads.com',
            mailDomains=[
                u'railroads.com',
            ],
        )
        self.ten_railroads = self.s_transit_todd.create_tenant(initial=data)

        # todd@transit.com creates user ray@railroads.com
        data = dict(
            username=u'ray',
            name=u'Ray',
            password=u'r',
            surname=u'R',
            mail=u'ray@railroads.com',
            tenant=self.ten_railroads,
            userServer=self.server1,
        )
        self.railroads_ray = self.s_transit_todd.create_user(initial=data)

        # get a session for ray@railroads.com
        self.s_railroads_ray = self.s.get_session(self.railroads_ray)

        # todd@transit.com grants ace on railroads.com to ray@railroads.com
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
            'user': self.railroads_ray.resourceUri,
        }
        self.s_transit_todd.add_tenant_ace(self.ten_railroads, data)



        # ray@railroads.com creates user rachel@railroads.com
        data = dict(
            username=u'rachel',
            name=u'Rachel',
            password=u'r',
            surname=u'R',
            mail=u'rachel@railroads.com',
            tenant=self.ten_railroads,
            userServer=self.server1,
        )
        self.railroads_rachel = self.s_railroads_ray.create_user(initial=data)

        # get a session for rachel@railroads.com
        self.s_railroads_rachel = self.s.get_session(self.railroads_rachel)

        # ray@railroads.com grants ace on railroads.com to rachel@railroads.com
        data = {
            'permissions': [
                'ViewUser',
                'WriteUser',
            ],
            'user': self.railroads_rachel.resourceUri,
        }
        self.s_railroads_ray.add_tenant_ace(self.ten_railroads, data)

        # rachel@railroads.com creates user roger@railroads.com
        data = dict(
            username=u'roger',
            name=u'Roger',
            password=u'r',
            surname=u'R',
            mail=u'roger@railroads.com',
            tenant=self.ten_railroads,
            userServer=self.server1,
        )
        self.railroads_roger = self.s_railroads_rachel.create_user(initial=data)


        ##############################################################
        ## Transit gets a new admin
        ##############################################################

        # todd@transit.com creates user tim@transit.com
        data = dict(
            username=u'tim',
            name=u'Tim',
            password=u't',
            surname=u'T',
            mail=u'tim@transit.com',
            tenant=self.ten_transit,
            userServer=self.server1,
        )
        self.transit_tim = self.s_transit_todd.create_user(initial=data)

        # get a session for tim@transit.com
        self.s_transit_tim = self.s.get_session(self.transit_tim)

        # todd@transit.com grants ace on bikes.com to tim@transit.com
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
            'user': self.transit_tim.resourceUri,
        }
        self.s_transit_todd.add_tenant_ace(self.ten_bikes, data)

        # tim@transit.com sets email domains for bikes.com
        self.ten_bikes.mailDomains.extend([
            u'bikes.org',
        ])
        self.s_transit_tim.update_tenant(self.ten_bikes)


    def unload(self):
        self.s_transit_todd.delete_tenant(self.ten_bikes)
        self.s_transit_todd.delete_tenant(self.ten_railroads)
        self.s_cloudy_clark.delete_tenant(self.ten_transit)
        self.s_cloudy_clark.delete_tenant(self.ten_pianos)
        self.s.delete_tenant(self.ten_cloudy)
