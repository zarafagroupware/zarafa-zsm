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

import ldap

from pumpkin import directory
from pumpkin import filters
from pumpkin import resource
from pumpkin.base import Model
from pumpkin.directory import ldap_exception_handler
from pumpkin.directory import ldap_reconnect_handler
from pumpkin.directory import log
from pumpkin.objectlist import ObjectList
from pumpkin.resource import ACTIVE_DIRECTORY_LDAP  # NOQA
from pumpkin.resource import LDAPResource
from pumpkin.resource import STANDARD_LDAP

from libzsm.datastructures import contains_list


class IntegrityError(Exception):
    pass


class Directory(directory.Directory):
    '''Subclass Directory so that we can set the trace_level in the initialize
    call.'''

    @directory.ldap_exception_handler
    def _connect(self):
        """Connect to LDAP server, does the actual work
        """
        directory.log.debug("Connecting to server '%s'" % self._resource.server)

        # NOTE: read from global sys.argv
        trace_level = 0
        if contains_list(sys.argv, ['-v', '3']):
            trace_level = 1

        self._ldapconn = directory.ldap.initialize(self._resource.server, trace_level=trace_level)

        self._ldapconn.protocol_version = directory.ldap.VERSION3
        self._ldapconn.set_option(directory.ldap.OPT_TIMEOUT, self._resource.timeout)
        self._ldapconn.set_option(
            directory.ldap.OPT_NETWORK_TIMEOUT, self._resource.timeout)

        self._start_tls()
        self._bind()
        self._read_schema()

    @ldap_reconnect_handler
    @ldap_exception_handler
    def add_object(self, ldap_dn, attrs):
        '''Overload to handle integrity error.'''

        log.debug("Creating new object '%s': %s" % (ldap_dn, attrs))
        modlist = []
        for (attr, values) in attrs.items():
            modlist.append((attr, values))

        try:
            self._ldapconn.add_s(self._encode(ldap_dn), modlist)
        except ldap.ALREADY_EXISTS as e:
            raise IntegrityError(e.message)

    @ldap_reconnect_handler
    @ldap_exception_handler
    def search(self, model, basedn=None, recursive=True, search_filter=None,
               skip_basedn=False, lazy=False):
        #HACK for base.get_children() - will be fixed in 0.2
        if model is None:
            model = Model

        ocs = []
        for oc in model.private_classes():
            if self._resource.server_type == resource.ACTIVE_DIRECTORY_LDAP:
                if oc in ["securityPrincipal"]:
                    continue  # Active Directory doesn't treat these as actually set
            ocs.append(filters.eq('objectClass', oc))
        model_filter = filters.opand(*ocs)

        if basedn is None:
            basedn = self._resource.basedn

        if recursive:
            scope = ldap.SCOPE_SUBTREE
        else:
            scope = ldap.SCOPE_ONELEVEL

        if search_filter:
            final_filter = filters.opand(model_filter, search_filter)
        else:
            final_filter = model_filter

        data = self._ldapconn.search_ext_s(
            self._encode(basedn),
            scope,
            final_filter,
            attrlist=model.ldap_attributes(lazy=lazy),
            timeout=self._resource.timeout,
        )

        ret = ObjectList()
        for (dn, attrs) in data:
            if skip_basedn and self._encode(dn) == self._encode(basedn):
                continue
            # filter out results of the wrong shape (AD returns a mix of dicts and lists)
            if type(attrs) == dict:
                ret.append(model(self, dn=dn, attrs=attrs))

        return ret


def get_directory_at(socket, user, password, basedn=None, use_tls=False,
                     server_type=STANDARD_LDAP):
    res = LDAPResource()
    res.server = socket
    res.login = user
    res.password = password
    res.basedn = basedn
    res.tls = use_tls
    res.server_type = server_type

    directory = Directory()
    directory.connect(res)

    return directory
