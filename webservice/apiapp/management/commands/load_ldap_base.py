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


from django.core.management.base import BaseCommand

from apiapp.models_ldap import Group
from apiapp.models_ldap import RootNode
from apiapp.models_ldap import Server
from apiapp.models_ldap import Tenant
from apiapp.models_ldap import Unit
from apiapp.models_ldap import User
from apiapp.permissions import PermissionStore

from conf.settings import config


class Command(BaseCommand):
    help = "Load base nodes into ldap."

    def handle(self, *args, **options):
        root_node = RootNode.load_root()

        u_ser = Unit(initial=dict(ou=u'servers'))
        u_ser.parent = root_node
        u_ser.save_or_update()

        u_ten = Unit(initial=dict(ou=u'tenants'))
        u_ten.parent = root_node
        u_ten.save_or_update()

        ## Servers

        ser = Server(initial=dict(
            cn=config.ZARAFA_SERVER1_NAME,
            ipHostNumber=config.ZARAFA_SERVER1_HOSTNAME,
            zarafaFilePath=config.ZARAFA_SERVER1_FILE_PATH,
            zarafaHttpPort=config.ZARAFA_SERVER1_HTTP_PORT,
            zarafaSslPort=config.ZARAFA_SERVER1_SSL_PORT,
        ))
        ser.save_or_update()

        ## Tenants

        ten = Tenant(initial=dict(o=config.ORIGIN_TENANT_NAME))
        ten.save_or_update()

        adm = User(initial=dict(
            uid=config.ORIGIN_ADMIN_USERNAME,
            cn=config.ORIGIN_ADMIN_USERNAME,
            sn=config.ORIGIN_ADMIN_USERNAME,
            userPassword=config.ORIGIN_ADMIN_PASSWORD,
            tenant=ten,
            zarafaUserServer=ser,
        ))
        adm.save_or_update()

        admins = Group(initial=dict(
            cn=u'admins',
            tenant=ten,
            member=[adm],
        ))
        perm_names = PermissionStore.get().get_all_names(is_priv=True)
        admins.set_privs(perm_names)
        admins.save_or_update()

        perm_names = PermissionStore.get().get_all_names(is_acl=True)
        ten.set_acl(perm_names, user=adm)
        ten.save()
