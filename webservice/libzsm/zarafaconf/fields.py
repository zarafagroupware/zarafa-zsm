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


class InvalidSettingValue(Exception):
    pass


class Setting(object):
    def __init__(self, name, default=None, required=False):
        self.name = name
        self.name_pretty = name.lower()
        self.default = default
        self.required = required

    def parse(self, value):
        try:
            return self.type(value)
        except ValueError:
            self.raise_invalid_value(value)

    def raise_invalid_value(self, value):
        raise InvalidSettingValue(
            u"Invalid value '{0}' for setting {1}[{2}]".format(
                value, self.name_pretty, self.type.__name__))


class BooleanSetting(Setting):
    type = bool

    def parse(self, value_str):
        value = None

        if value_str == 'true':
            value = True
        elif value_str == 'false':
            value = False

        if value is not None:
            return value

        self.raise_invalid_value(value_str)


class IntegerSetting(Setting):
    type = int


class StringSetting(Setting):
    type = unicode


class StringListSetting(Setting):
    type = list

    def parse(self, value_str):
        try:
            value = re.split(',\s*', value_str)
            value = [unicode(s) for s in value]
            return value
        except ValueError:
            self.raise_invalid_value(value_str)


class LdapSocket(StringSetting):
    def parse(self, value):
        if not value.startswith(('ldap://', 'ldapi://')):
            self.raise_invalid_value(value)

        return super(LdapSocket, self).parse(value)
