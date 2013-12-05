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


import re

from permissions import PermissionStore


class Ace(object):
    def __init__(self, perms, user_id=None, group_id=None):
        assert user_id or group_id

        self.perms = perms

        self.user_id = user_id
        self.group_id = group_id

    def __repr__(self):
        return '<{0}: {1} {2} {3}>'.format(
            self.__class__.__name__,
            'usr' if self.user_id else 'grp',
            self.user_id or self.group_id,
            self.perms)

    def has_perm(self, perm, principal):
        perm_name = perm if isinstance(perm, basestring) else perm.name

        val = False
        if perm_name in self.perms:
            if self.group_id:
                val = principal.zarafaId == self.group_id
            else:
                val = principal.zarafaId == self.user_id

        return val

    def format(self):
        perms = sorted(self.perms)
        principal_key = 'grp' if self.group_id else 'usr'
        principal_id = self.group_id if self.group_id else self.user_id
        line = u'{0}:{1} perms:{2}'.format(
            principal_key, principal_id, ','.join(perms))
        return line

    @classmethod
    def parse(cls, line):
        type, id, perms = re.findall('^(usr|grp):([0-9a-z]+) perms:(.*)$', line)[0]
        perms = perms.split(',')

        # drop any invalid perms
        perms = PermissionStore.filter_valid(perms)

        kwargs = {}
        if type == 'usr':
            kwargs = {'user_id': id}
        elif type == 'grp':
            kwargs = {'group_id': id}

        self = cls(perms, **kwargs)
        return self


class Acl(object):
    def __init__(self, aces):
        self.aces = aces

    def has_perm(self, perm, principal):
        for ace in self.aces:
            if ace.has_perm(perm, principal):
                return True
        return False

    def format(self):
        lines = [ace.format() for ace in self.aces]
        return lines

    @classmethod
    def parse(cls, lst):
        aces = [Ace.parse(i) for i in lst]

        self = cls(aces)
        return self


class Privileges(object):
    def __init__(self, perms):
        self.perms = perms

    def format(self):
        perms = sorted(self.perms)
        line = u','.join(perms)
        return [line]

    def has_perm(self, perm):
        return perm.name in self.perms

    @classmethod
    def parse(cls, line):
        try:
            line = line[0]
        except IndexError:
            line = ''

        perms = line.split(',') if line else []

        # drop any invalid perms
        perms = PermissionStore.filter_valid(perms)

        perms = sorted(perms)
        self = cls(perms)
        return self
