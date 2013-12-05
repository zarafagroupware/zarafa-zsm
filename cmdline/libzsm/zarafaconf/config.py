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


import os
import re

from fields import InvalidSettingValue


class ZarafaConfig(object):
    re_key = '[0-9a-z_]+'
    rx_key_value_line = re.compile('(?m)^(' + re_key + ')[ \t]*=[ \t]*(.*)$')

    def __init__(self, zconf_path=None, settings=None):
        self.zconf_path = zconf_path
        self.settings = {}
        self._zconf_settings = None

        for item in settings:
            self.settings[item.name] = item

    def have_zconf(self):
        return os.path.isfile(self.zconf_path)

    def _read_all_from_zconf(self):
        pairs = []

        if self.have_zconf():
            content = open(self.zconf_path, 'rt').read()
            pairs = re.findall(self.rx_key_value_line, content)

        return pairs

    @property
    def zconf_settings(self):
        if self._zconf_settings is None:
            self._zconf_settings = {}
            pairs = self._read_all_from_zconf()
            for key, value in pairs:
                self._zconf_settings[key] = value
        return self._zconf_settings

    def get_unknown_zconf_keys(self):
        valid = set([k.lower() for k in self.settings.keys()])
        actual = set(self.zconf_settings.keys())
        unknowns = actual - valid
        return unknowns

    def get_known_zconf_keys(self):
        zconf_keys = set(self.zconf_settings.keys())
        invalid = self.get_unknown_zconf_keys()
        keys = zconf_keys - invalid
        return keys

    def get_invalid_zconf_keys(self):
        keys = self.get_known_zconf_keys()

        invalids = set()
        for key in keys:
            try:
                self._get(key.upper())
            except InvalidSettingValue as e:
                invalids.add((key, e))

        return invalids

    def get_missing_zconf_keys(self):
        missing = set()

        for setting in self.settings.values():
            if setting.required:
                key = setting.name.lower()
                if not self.zconf_settings.get(key):
                    missing.add(key)

        return missing

    def _get(self, key):
        setting = self.settings[key]

        value = None
        value_str = self.zconf_settings.get(key.lower())

        if value_str is not None:
            value = setting.parse(value_str)

        if value is None and not setting.default is None:
            if callable(setting.default):
                value = setting.default()
            else:
                value = setting.default

        return value

    def __getitem__(self, key):
        return self._get(key)

    def __getattr__(self, key):
        try:
            return self._get(key)
        except KeyError:
            raise AttributeError
