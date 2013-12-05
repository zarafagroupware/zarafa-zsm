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


from libzsm.zarafaconf import BooleanSetting
from libzsm.zarafaconf import IntegerSetting
from libzsm.zarafaconf import LdapSocket
from libzsm.zarafaconf import StringSetting
from libzsm.zarafaconf import ZarafaConfig

import os


class ZarafaSocket(StringSetting):
    def parse(self, value):
        if not value.startswith(('file://', 'http://', 'https://')):
            self.raise_invalid_value(value)

        return super(ZarafaSocket, self).parse(value)


config = ZarafaConfig(
    zconf_path='/etc/zarafa/zsm-server.cfg',

    settings=[
        # Webservice url
        StringSetting('API_BASE_URL', required=True,
                      default='http://localhost:8000/api/v1/'),

        # Enable formated json output when viewing urls in a browser
        BooleanSetting('ENABLE_API_DEBUG_VIEW', default=True),

        # Ldap settings
        LdapSocket('LDAP_SOCKET', required=True, default='ldap://localhost:389'),
        StringSetting('LDAP_LOGIN', required=True, default='cn=admin,dc=zarafa'),
        StringSetting('LDAP_PASSWORD', required=True, default='zarafa'),
        BooleanSetting('LDAP_TLS', default=False),
        StringSetting('LDAP_BASEDN', required=True, default='dc=zarafa'),

        # Zarafa settings
        ZarafaSocket('ZARAFA_SOCKET', required=True,
                     #default=lambda: os.getenv('ZARAFA_SOCKET', 'file:///var/run/zarafa')),
                     default=lambda: os.getenv('ZARAFA_SOCKET', 'https://127.0.0.1:237/')),
        StringSetting('ZARAFA_ADMIN_USERNAME', required=True, default='SYSTEM'),
        StringSetting('ZARAFA_ADMIN_PASSWORD', required=True, default='SYSTEM'),
        StringSetting('ZARAFA_SSLKEY_FILE', default='/etc/zarafa/sslkeys/client.pem'),
        StringSetting('ZARAFA_SSLKEY_PASS', default='zarafa'),

        # Server settings
        StringSetting('ZARAFA_SERVER1_NAME', required=True, default=u'zarafa1'),
        StringSetting('ZARAFA_SERVER1_HOSTNAME', required=True, default=u'127.0.0.1'),
        StringSetting('ZARAFA_SERVER1_FILE_PATH', required=True, default=u'/var/run/zarafa'),
        IntegerSetting('ZARAFA_SERVER1_HTTP_PORT', required=True, default=236),
        IntegerSetting('ZARAFA_SERVER1_SSL_PORT', default=237),

        # Auth settings
        StringSetting('ORIGIN_TENANT_NAME', required=True, default=u'origin'),
        StringSetting('ORIGIN_ADMIN_USERNAME', required=True, default=u'admin'),
        StringSetting('ORIGIN_ADMIN_PASSWORD', required=True, default=u'a'),
    ],
)
