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


from fabric.api import env
from fabric.api import task

import actions
from fab import ws


@task
def restart():
    '''Restart slapd service'''
    actions.restart()


@task
def dumpdata():
    '''Dump the ldap tree to stdout'''
    env.run('ldapsearch -x -b {0} -LLL'.format(env.ldap_dit_dn))


@task
def setup():
    '''Sets up the database, loads modules and schema + populates base data.'''
    actions.load_schema()
    actions.create_database()
    actions.load_modules()
    actions.populate_database()

@task
def setup_config():
    '''Sets up the database, loads modules and schema.'''
    actions.load_schema()
    actions.create_database()
    actions.load_modules()


@task
def teardown(stop=False):
    '''Deletes the database, unloads modules and schema.'''
    actions.delete_database_storage()
    actions.drop_database()
    actions.unload_modules()
    actions.unload_schema()
    if stop:
        actions.stop()
    else:
        restart()


@task
def recreate(nofixtures=False):
    '''Teardown + Setup ldap + Load demo data'''
    teardown()
    setup()
    ws.load_basedata()
    if not nofixtures:
        ws.load_demodata()
    dumpdata()

@task
def recreate_config():
    '''teardown + setup_config'''
    teardown()
    setup_config()
