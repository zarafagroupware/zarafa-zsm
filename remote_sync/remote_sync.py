#!/usr/bin/env python
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


import sys
sys.path.append('..')

EXTRA_PATHS = []

for p in EXTRA_PATHS:
    sys.path.append(p)


from optparse import OptionParser
import logging

import pumpkin.exceptions

from libzsm.pumpkin_ext.directory import get_directory_at
from libzsm.rest_client import exc as httpexc
from libzsm.rest_client.api import Api
from libzsm.rest_client.logutils import get_logger
from libzsm.system import stdio

from conf.remote_settings import remote_config
from conf.settings import config
from models import ModelBuilder


def get_api():
    api = Api(
        config.API_BASE_URL,
        basic_auth=(
            u'{0}@{1}'.format(
                config.ORIGIN_ADMIN_USERNAME,
                config.ORIGIN_TENANT_NAME,
            ),
            config.ORIGIN_ADMIN_PASSWORD,
        ),
    )
    return api


class RemoteSync(object):
    def __init__(self, options):
        self.options = options

        self.remote_config = remote_config
        self.remote_config.zconf_path = self.options.cfg

        if self.options.verbose:
            logger = get_logger(__file__)
            logger.setLevel(logging.DEBUG)

        self.api = get_api()

    @property
    def server1(self):
        if not getattr(self, '_server1', None):
            self._server1 = self.api.get_server(name=config.ZARAFA_SERVER1_NAME)
        return self._server1

    @property
    def remote_dir(self):
        if not getattr(self, '_remote_dir', None):
            self._remote_dir = get_directory_at(
                self.remote_config.REMOTE_LDAP_SOCKET,
                self.remote_config.REMOTE_LDAP_LOGIN,
                self.remote_config.REMOTE_LDAP_PASSWORD,
                server_type=self.remote_config.REMOTE_LDAP_TYPE)
        return self._remote_dir

    def post_process_remote_objs(self, objs):
        for obj in objs:
            # For AD hexify binary blobs
            if self.remote_config.REMOTE_LDAP_TYPE == 'ad':
                remote_field_name = obj.__class__.remoteId
                value = obj._storage[remote_field_name][0].encode('hex')
                obj.remoteId = unicode(value)

            # make sure surname is set (mandatory field)
            if isinstance(obj, self.User) or isinstance(obj, self.Contact):
                if not obj.name:
                    obj.name = obj.username
                if not obj.surname:
                    obj.surname = obj.name

    def serialize_values(self, remote_obj, dest):
        for fname in remote_obj._get_fields().keys():
            value = getattr(remote_obj, fname)

            dest[fname] = value

        return dest

    def fmt_remote(self, friendly_name, remoteId):
        return u'{0} [remoteId {1}]'.format(friendly_name, remoteId)

    def sync_object(self, resource_name,
                    remote_obj, initial, friendly_name,
                    create_method, get_method, update_method):

        kwargs = {}
        tenant = initial.get('tenant')
        if tenant:
            kwargs.update(dict(
                tenant=tenant,
            ))

        def format_remote():
            return self.fmt_remote(friendly_name, initial['remoteId'])

        obj = None
        try:
            obj = get_method(remoteId=initial['remoteId'], **kwargs)

            if obj.remoteChangedDate < remote_obj.remoteChangedDate:
                stdio.warn(u'{0} {1} out of date, updating'.format(
                    resource_name, format_remote()))
                obj.update_with(initial)
                update_method(obj)

            else:
                stdio.ok(u'{0} {1} is up to date'.format(resource_name, format_remote()))

        except httpexc.ObjectDoesNotExist:
            stdio.warn(u'{0} {1} not found, creating'.format(resource_name, format_remote()))

            try:
                obj = create_method(initial=initial)
            except httpexc.Http400 as e:
                stdio.error(u'Failed to create {0} {1} with: {2}'.format(
                    resource_name, format_remote(), e))

        return obj

    def sync_tenant(self, remote_tenant):
        initial = {}

        initial = self.serialize_values(remote_tenant, initial)

        tenant = self.sync_object(
            'Tenant',
            remote_tenant, initial, initial['name'],
            self.api.create_tenant, self.api.get_tenant, self.api.update_tenant,
        )

        return tenant

    def sync_user(self, tenant, remote_user):
        initial = dict(
            tenant=tenant,
            userServer=self.server1,
        )

        initial = self.serialize_values(remote_user, initial)

        user = self.sync_object(
            'User',
            remote_user, initial, initial['username'],
            self.api.create_user, self.api.get_user, self.api.update_user,
        )

        return user

    def sync_group(self, tenant, remote_group, by_dn, by_remoteId):
        initial = dict(
            tenant=tenant,
        )

        initial = self.serialize_values(remote_group, initial)

        # resolve user dn's
        for i, dn in enumerate(initial['members']):
            remote_user = by_dn.get(dn)
            if remote_user:
                user = by_remoteId.get(remote_user.remoteId)
                if user:
                    initial['members'][i] = user

        group = self.sync_object(
            'Group',
            remote_group, initial, initial['name'],
            self.api.create_group, self.api.get_group, self.api.update_group,
        )

        return group

    def sync_contact(self, tenant, remote_contact):
        initial = dict(
            tenant=tenant,
        )

        initial = self.serialize_values(remote_contact, initial)

        contact = self.sync_object(
            'Contact',
            remote_contact, initial, initial['name'],
            self.api.create_contact, self.api.get_contact, self.api.update_contact,
        )

        return contact

    def filter_objects(self, tenant,
                       resource_name,
                       remote_objects, friendly_name_key,
                       all_method, delete_method):
        if remote_objects:
            remote_ids = [r.remoteId for r in remote_objects]

            objects = all_method(tenant=tenant)
            for obj in objects:
                if obj.remoteId and obj.remoteId not in remote_ids:
                    fmt_obj = self.fmt_remote(
                        getattr(obj, friendly_name_key), getattr(obj, 'remoteId'))
                    stdio.warn(u'{0} {1} was removed on remote, deleting'.format(
                        resource_name, fmt_obj))
                    delete_method(obj)

    def filter_contacts(self, tenant, remote_contacts):
        return self.filter_objects(tenant,
                                   'Contact',
                                   remote_contacts, 'name',
                                   self.api.all_contact, self.api.delete_contact)

    def filter_groups(self, tenant, remote_groups):
        return self.filter_objects(tenant,
                                   'Group',
                                   remote_groups, 'name',
                                   self.api.all_group, self.api.delete_group)

    def filter_users(self, tenant, remote_users):
        return self.filter_objects(tenant,
                                   'User',
                                   remote_users, 'username',
                                   self.api.all_user, self.api.delete_user)

    def process_tenant(self, dn):
        remote_tenants = []
        try:
            remote_tenants = self.remote_dir.search(
                self.Tenant,
                basedn=dn,
                search_filter=self.remote_config.TENANT_EXTRA_FILTER,
            )
            self.post_process_remote_objs(remote_tenants)
        except pumpkin.exceptions.ObjectNotFound:
            stdio.error(u'Tenant {0} not found on remote'.format(dn))
            return

        if remote_tenants:
            remote_tenant = remote_tenants[0]

            remote_users = self.remote_dir.search(
                self.User,
                remote_tenant.dn,
                search_filter=self.remote_config.USER_EXTRA_FILTER,
            )
            self.post_process_remote_objs(remote_users)

            remote_groups = self.remote_dir.search(
                self.Group,
                remote_tenant.dn,
                search_filter=self.remote_config.GROUP_EXTRA_FILTER,
            )
            self.post_process_remote_objs(remote_groups)

            remote_contacts = self.remote_dir.search(
                self.Contact,
                remote_tenant.dn,
                search_filter=self.remote_config.CONTACT_EXTRA_FILTER,
            )
            self.post_process_remote_objs(remote_contacts)

            ## Sync stage

            tenant = self.sync_tenant(remote_tenant)
            users = [self.sync_user(tenant, u) for u in remote_users]

            by_dn = dict([(u.dn, u) for u in remote_users])
            by_remoteId = dict([(u.remoteId, u) for u in users])

            [self.sync_group(tenant, g, by_dn, by_remoteId) for g in remote_groups]
            [self.sync_contact(tenant, c) for c in remote_contacts]

            ## Remove stale stage

            self.filter_users(tenant, remote_users)
            self.filter_groups(tenant, remote_groups)
            self.filter_contacts(tenant, remote_contacts)

    def sync(self):
        builder = ModelBuilder(self.remote_config)

        self.Contact = builder.get_contact()
        self.Group = builder.get_group()
        self.User = builder.get_user()
        self.Tenant = builder.get_tenant()

        for dn in [self.remote_config.TENANT_DN]:
            self.process_tenant(dn)


if __name__ == '__main__':
    parser = OptionParser()
    parser.description = "Synchronize remote Active Directory/LDAP -> ZSM (unidirectional)."

    parser.add_option('-c', dest='cfg', metavar='cfg', action='store', help='Config file')
    parser.add_option('-v', dest='verbose', action='store_true', help='Verbose mode')
    options, args = parser.parse_args()

    if not options.cfg:
        stdio.die(u'No config file supplied.')

    remotesync = RemoteSync(options)
    remotesync.sync()
