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


from os.path import join

from fabric.api import env
from fabric.api import local

from fab.proc import hacked_sudo
from fab import apache  # NOQA
from fab import deps  # NOQA
from fab import ldap  # NOQA
from fab import pkg  # NOQA
from fab import qa  # NOQA
from fab import ws  # NOQA
from fab import zcp  # NOQA


env.hosts = ['localhost']
env.run = local
env.sudo = hacked_sudo

## LDAP
env.ldap_database_name = 'zarafa'

env.ldap_dit_dn = 'dc=zarafa'
env.ldap_admin_dn = 'cn=admin,{0}'.format(env.ldap_dit_dn)
env.ldap_admin_pw = 'zarafa'

env.ldap_config_dn = 'cn=config'
env.ldap_schema_dn = 'cn=schema,{0}'.format(env.ldap_config_dn)
env.ldap_custom_schema_cn = 'zarafa'
env.ldap_custom_schema_dn = 'cn=zarafa,{0}'.format(env.ldap_schema_dn)
env.ldap_modules = ['memberof', 'refint']
env.ldap_group_objectclass = 'zarafa-group'
env.ldap_indexes = {
    'cn':                       'pres,eq,sub',
    'gidNumber':                'pres,eq',
    'mail':                     'pres,eq,sub',
    'memberUid':                'pres,eq',
    'o':                        'pres,eq',
    'objectClass':              'pres,eq',
    'ou':                       'pres,eq',
    'sn':                       'pres,eq,sub',
    'uid':                      'pres,eq',
    'uidNumber':                'pres,eq',
    'zarafaAccount':            'pres,eq',
    'zarafaAliases':            'pres,eq,sub',
    'zarafaId':                 'eq',
    'zarafaRemoteId':           'eq',
    'zarafaSendAsPrivilege':    'pres,eq',
    'zarafaSoftDeletedDate':    'pres,eq',
    'zarafaViewPrivilege':      'pres,eq',
}

env.ldap_object_type_attribute = 'objectClass'
env.ldap_user_object_class = 'zarafa-user'
env.ldap_group_object_class = 'zarafa-group'
env.ldap_contact_object_class = 'zarafa-contact'
env.ldap_company_object_class = 'zarafa-company'
env.ldap_addresslist_object_class = 'zarafa-addresslist'
env.ldap_dynamicgroup_object_class = 'zarafa-dynamicgroup'
env.ldap_server_object_class = 'ipHost'
env.ldap_user_search_filter = ''
env.ldap_user_unique_attribute = 'uid'
env.ldap_loginname_attribute = 'uid'
env.ldap_company_unique_attribute = 'o'
env.ldap_companyname_attribute = 'o'

env.ldap_template_dir = 'etc'
env.ldap_schema_dir = join(env.ldap_template_dir, 'schema')
env.ldap_ref_attributes = [
    'zarafaAdminPrivilege',
    'zarafaQuotaCompanyWarningRecipients',
    'zarafaQuotaUserWarningRecipients',
    'zarafaSendAsPrivilege',
    'zarafaSystemAdmin',
    'zarafaViewPrivilege',
]

## ZCP
env.zcp_mysql_dbname = 'zarafa'

env.zcp_fakeroot_dirname = 'fakeroot'
env.zcp_repo_basedir_dirname = 'zcp'

env.zcp_server_cfg = {
    'attachment_storage': 'database',
    'audit_log_enabled': 'yes',
    'audit_log_method': 'file',
    'enable_hosted_zarafa': 'true',
    'log_level': '5',
    'loginname_format': '%u@%c',
    'server_tcp_port': '236',
    #'storename_format': '%u@%c',
    'storename_format': '%f',
    'user_plugin': 'ldapms',

    # multiserver settings
    'enable_distributed_zarafa': 'true',  # true gives MAPI_E_LOGON_FAILED
    'server_name': 'zarafa1',  # required for distributed zarafa

    # ssl settings
    'server_ssl_enabled': 'yes',  # vm testing
    'server_ssl_port': '237',
    'server_ssl_key_pass': 'zarafa',
}

env.zcp_ldap_cfg = {
    'ldap_bind_user': env.ldap_admin_dn,
    'ldap_bind_passwd': env.ldap_admin_pw,
    'ldap_search_base': env.ldap_dit_dn,

    'ldap_object_type_attribute': env.ldap_object_type_attribute,
    'ldap_user_type_attribute_value': env.ldap_user_object_class,
    'ldap_group_type_attribute_value': env.ldap_group_object_class,
    'ldap_contact_type_attribute_value': env.ldap_contact_object_class,
    'ldap_company_type_attribute_value': env.ldap_company_object_class,
    'ldap_addresslist_type_attribute_value': env.ldap_addresslist_object_class,
    'ldap_dynamicgroup_type_attribute_value': env.ldap_dynamicgroup_object_class,
    'ldap_server_type_attribute_value': env.ldap_server_object_class,

    'ldap_user_search_filter': env.ldap_user_search_filter,
    'ldap_user_unique_attribute': env.ldap_user_unique_attribute,
    'ldap_loginname_attribute': env.ldap_loginname_attribute,

    'ldap_company_unique_attribute': env.ldap_company_unique_attribute,
    'ldap_companyname_attribute': env.ldap_companyname_attribute,
}

## PYPI

# cache dir is per-user to work around permission problems
env.pypi_package_download_cache = '/tmp/pypi-cache-{username}'
