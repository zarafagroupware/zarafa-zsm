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


from libzsm.zarafaconf import LdapSocket
from libzsm.zarafaconf import StringSetting
from libzsm.zarafaconf import StringListSetting
from libzsm.zarafaconf import ZarafaConfig


remote_config = ZarafaConfig(
    settings=[
        # Remote LDAP settings
        LdapSocket('REMOTE_LDAP_SOCKET', required=True),
        StringSetting('REMOTE_LDAP_LOGIN', required=True),
        StringSetting('REMOTE_LDAP_PASSWORD', required=True),
        StringSetting('REMOTE_LDAP_TYPE', required=True),

        # Tenants to sync settings
        StringSetting('TENANT_DN', required=True),

        # Common attribute settings
        StringSetting('COMMON_REMOTE_ID', required=True),
        StringSetting('COMMON_REMOTE_CHANGED_DATE', required=True),

        # Tenant attribute settings
        StringListSetting('TENANT_OBJECT_CLASSES', required=True),
        StringSetting('TENANT_EXTRA_FILTER'),
        StringSetting('TENANT_NAME', required=True),

        # User attribute settings
        StringListSetting('USER_OBJECT_CLASSES', required=True),
        StringSetting('USER_EXTRA_FILTER'),
        StringSetting('USER_USERNAME', required=True),
        StringSetting('USER_SURNAME', required=True),
        StringSetting('USER_NAME', required=True),
        StringSetting('USER_MAIL', required=True),
        StringSetting('USER_INITIALS'),
        StringSetting('USER_DESCRIPTION'),

        # Group attribute settings
        StringListSetting('GROUP_OBJECT_CLASSES', required=True),
        StringSetting('GROUP_EXTRA_FILTER'),
        StringSetting('GROUP_NAME', required=True),
        StringSetting('GROUP_MEMBERS', required=True),

        # Contact attribute settings
        StringListSetting('CONTACT_OBJECT_CLASSES', required=True),
        StringSetting('CONTACT_EXTRA_FILTER'),
        StringSetting('CONTACT_SURNAME', required=True),
        StringSetting('CONTACT_NAME', required=True),
        StringSetting('CONTACT_MAIL', required=True),
    ],
)
