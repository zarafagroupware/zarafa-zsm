#!/usr/bin/env python
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



import sys

EXTRA_PATHS = []

for p in EXTRA_PATHS:
    sys.path.append(p)


from optparse import OptionParser
import logging

from conf.settings import config
from libzsm.rest_client.api import Api
from libzsm.rest_client import logutils
logger = logutils.get_logger(__file__)


def write(msg):
    sys.stdout.write(msg+'\n')
    sys.stdout.flush()

class Client(object):
    def __init__(self):
        self.api = Api(config.API_BASE_URL)

    ## Tenants

    def list_tenants(self):
        tenants = self.api.tenants.all()

        fmt = '{0}'

        propnames = ['name']
        ss = [fmt.format(*propnames)]
        ss.append(78 * '-')
        for tenant in tenants:
            propvals = [getattr(tenant, prop) for prop in propnames]
            ss.append(fmt.format(*propvals))

        s = '\n'.join(ss)
        write(s)

    def view_tenant(self, id):
        tenant = self.api.tenants.get(name=id)
        write(tenant.pprint())

    def create_tenant(self, tenantName, att_list=None):
        atts = self.decode_att_list(att_list)
        atts.update({
            'tenantName': tenantName,
        })
        #atts = self.prepare_atts('tenants', atts)
        self.api.tenants.create(initial=atts)

    def update_tenant(self, id, att_list=None):
        atts = self.decode_att_list(att_list)
        #atts = self.prepare_atts('tenants', atts)

        tenant = self.api.tenants.get(tenantName=id)
        tenant.update_with(atts)

        self.api.tenants.update(tenant)

    def delete_tenant(self, id):
        tenant = self.api.tenants.get(tenantName=id)
        self.api.tenants.delete(tenant)

    ## Users

    def _rewrite_atts_for_tenant(self, atts):
        tenantName = atts.get('tenant')
        if tenantName:
            tenant = self.api.tenants.get(tenantName=tenantName)
            atts['tenant'] = tenant
            return atts
        return atts

    def list_users(self):
        users = self.api.users.all()

        fmt = '{0:16} {1}'

        propnames = ['username', 'tenant']
        ss = [fmt.format(*propnames)]
        ss.append(78 * '-')
        for user in users:
            propvals = [getattr(user, prop) for prop in propnames]
            ss.append(fmt.format(*propvals))

        s = '\n'.join(ss)
        write(s)

    def view_user(self, id):
        user = self.api.users.get(username=id)
        write(user.pprint())

    def create_user(self, username, att_list=None):
        atts = self.decode_att_list(att_list)
        atts.update({
            'username': username,
        })
        #atts = self.prepare_atts('users', atts)

        atts = self._rewrite_atts_for_tenant(atts)

        self.api.users.create(initial=atts)

    def update_user(self, id, att_list=None):
        atts = self.decode_att_list(att_list)
        #atts = self.prepare_atts('users', atts)

        atts = self._rewrite_atts_for_tenant(atts)

        user = self.api.users.get(username=id)
        user.update_with(atts)

        self.api.users.update(user)

    def delete_user(self, id):
        user = self.api.users.get(username=id)
        self.api.users.delete(user)

    ## Helper methods

    def decode_att_list(self, att_list):
        if not att_list:
            return {}
        return dict([att.split('=') for att in att_list])

    def _prepare_atts(self, resource_name, atts):
        '''Check all attributes against the schema, try to cast values to the
        schema type.'''
        schema = self.call_api('/{0}/schema/'.format(resource_name))
        fields = schema.get('fields', [])
        if not fields:
            logger.error('Failed to fetch schema for: {0}'.format(resource_name))
            sys.exit(1)

        for att, val in atts.items():
            if not att in fields:
                logger.error('Invalid attribute: {0}'.format(att))
                sys.exit(1)

            else:
                typ = fields[att].get('type')
                if typ in ['integer', 'list']:
                    try:
                        atts[att] = eval(val)
                    except:
                        logger.error('Invalid value for {0}: {1}'.format(att, val))
                        sys.exit(1)

        return atts



if __name__ == '__main__':
    parser = OptionParser()

    parser.add_option('-l', dest='list_users', action='store_true', help='List users')
    parser.add_option('-s', dest='view_user', metavar='username', action='store', help='View user')
    parser.add_option('-c', dest='create_user', metavar='username', action='store', help='Create user')
    parser.add_option('-u', dest='update_user', metavar='username', action='store', help='Update user')
    parser.add_option('-d', dest='delete_user', metavar='username', action='store', help='Delete user')

    parser.add_option('--list-tenants', dest='list_tenants', action='store_true', help='List tenants')
    parser.add_option('--view-tenant', dest='view_tenant', metavar='tenantName', action='store', help='View tenant')
    parser.add_option('--create-tenant', dest='create_tenant', metavar='tenantName', action='store', help='Create tenant')
    parser.add_option('--delete-tenant', dest='delete_tenant', metavar='tenantName', action='store', help='Delete tenant')
    parser.add_option('--update-tenant', dest='update_tenant', metavar='tenantName', action='store', help='Update tenant')

    parser.add_option('--set', dest='atts', metavar='att=val', action='append', help='Set attribute: att=val')

    parser.add_option('-v', dest='verbose', action='store_true', help='Run in verbose mode')
    options, args = parser.parse_args()

    if options.verbose:
        logger.setLevel(logging.DEBUG)

    client = Client()

    if options.list_users:
        client.list_users()

    elif options.view_user:
        client.view_user(options.view_user)

    elif options.create_user:
        client.create_user(username=options.create_user, att_list=options.atts)

    elif options.update_user:
        client.update_user(options.update_user, att_list=options.atts)

    elif options.delete_user:
        client.delete_user(options.delete_user)


    elif options.list_tenants:
        client.list_tenants()

    elif options.view_tenant:
        client.view_tenant(options.view_tenant)

    elif options.create_tenant:
        client.create_tenant(tenantName=options.create_tenant, att_list=options.atts)

    elif options.update_tenant:
        client.update_tenant(options.update_tenant, att_list=options.atts)

    elif options.delete_tenant:
        client.delete_tenant(options.delete_tenant)


    # no action given
    else:
        parser.print_help()
        sys.exit(1)
