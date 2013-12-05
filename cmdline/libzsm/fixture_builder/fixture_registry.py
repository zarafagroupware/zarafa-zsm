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


from collections import defaultdict

from base import mutate


class FixtureRegistry(object):
    def __init__(self):
        self.store = defaultdict(list)

    def register(self, resource_name, fixture):
        # XXX to prevent double registration, make sure the path
        # of the module the fixture lives in is libzsm directly
        #if 'cmdline.libzsm' in fixture.__module__:
        #    return

        if not fixture in self.store[resource_name]:
            self.store[resource_name].append(fixture)

    def get_single_fixture_by_id(self, id):
        for fixtures in self.store.values():
            for fix in fixtures:
                i = getattr(getattr(fix, 'id', None), 'pk', None)
                if id == i:
                    return fix

    def get_single_fixture(self, resource_name):
        try:
            return self.store[resource_name][0]
        except IndexError:
            pass

    def get_fixtures(self, *args):
        dct = {}
        for resource_name in args:
            dct[resource_name] = self.store[resource_name]
        return dct

    def get_fixtures_mutated(self, *args):
        dct = self.get_fixtures(*args)
        new_dct = defaultdict(list)

        for resource_name, fixtures in dct.items():
            for fixture in fixtures:

                new_fixture = fixture

                # don't mutate preloaded
                if not getattr(fixture, '_is_preloaded', False):
                    new_fixture = mutate(fixture)

                new_dct[resource_name].append(new_fixture)

        return new_dct

registry = FixtureRegistry()
