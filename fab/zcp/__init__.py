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

from fab import fs
from fab.models.zcpenv import ZcpEnv
import actions


@task
def start():
    '''Starts zcp services'''
    actions.start_services()


@task
def stop():
    '''Stop zcp services'''
    actions.stop_services()


@task
def setup():
    '''Patches config files, recreates mysql db, starts zcp services'''
    actions.patch_config()
    actions.drop_mysql_database()
    actions.start_services()


@task
def teardown():
    '''Stops zcp services'''
    actions.stop_services()


@task
def recreate():
    ''' Teardown + Setup '''
    teardown()
    setup()


@task
def load_local_zcp():
    '''Set up system wide paths/env vars to run zcp from a local checkout'''
    actions.setup_local_zcp()


@task
def imysql():
    '''Launch a mysql shell.'''

    zcpenv = ZcpEnv.get()

    env.run('mysql -u {0} -p{1} {2}'.format(
        zcpenv.mysql_user,
        zcpenv.mysql_password,
        env.zcp_mysql_dbname,
    ))


@task
def ipython(userid='SYSTEM', password='secret'):
    '''Launch an ipython shell.'''

    snip = '''
import os
from MAPI.Util import OpenECSession
from MAPI.Util import GetDefaultStore

def get_session(userid, password):
    global socket
    if userid == 'SYSTEM':
        #session = OpenECSession('demo1', 'zarafa', 'http://192.168.50.195:236')
        #session = OpenECSession('SYSTEM', '', 'http://192.168.50.195:236')
        socket = 'file:///var/run/zarafa'
    else:
        port = 236 if os.getuid() == 0 else 2236
        socket = 'http://localhost:%s' % port

    return OpenECSession(userid, password, socket)

userid = '{userid}'
password = '{password}'
session = get_session(userid, password)
store = GetDefaultStore(session)
print
fmt = "%-12s  %s"
print fmt % ("userid:", userid)
print fmt % ("password:", password)
print fmt % ("socket:", socket)
print fmt % ("session:", session)
print fmt % ("store:", store)
'''
    with fs.mkstemp() as fp:
        snip = snip.format(
            userid=userid,
            password=password,
        )

        open(fp, 'wt').write(snip)

        print(snip)
        interpreter = 'ipython' if fs.sh_which('ipython') else 'python'
        env.run('{0} -i {1}'.format(interpreter, fp))
