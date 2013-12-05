#!/usr/bin/python
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
import shutil
import signal
import subprocess
import sys
import time

from libzsm.system.proc import invoke
from libzsm.system import stdio

RUNSERVER_PORT = 8000


def halt_runserver():
    def find_pid():
        line = invoke("netstat --inet -ln -p 2>/dev/null | egrep '^tcp' | grep ':%s'" %
                      RUNSERVER_PORT, shell=True, capture=True)
        tup = re.findall('([0-9]+)[/]python', line)
        if tup:
            pid = int(tup[0])
            return pid

    pid = find_pid()
    if pid:
        stdio.write('Waiting for process pid {0} to exit'.format(pid))

    while pid:
        stdio.write('.')
        os.kill(pid, signal.SIGTERM)

        time.sleep(.5)
        pid = find_pid()
    stdio.write('\n')

def main():
    # halt runserver if running on the same port
    halt_runserver()

    # garbage collect any old coverage data
    invoke(['coverage', 'erase'])
    invoke(['coverage', 'erase'], cwd='webservice')

    # startup runserver
    args = ['coverage', 'run', '--source', '.',
            'manage.py', 'runserver', '0.0.0.0:%s' % RUNSERVER_PORT, '--noreload']
    proc_server = subprocess.Popen(args, cwd='webservice')
    time.sleep(1)

    # run the tests
    invoke(['./runtests.py', '--cov'] + sys.argv[1:])  # pass on sys.argv

    # teardown runserver
    proc_server.send_signal(signal.SIGINT)
    proc_server.wait()

    # collect all coverage files into one
    shutil.move('webservice/.coverage', '.coverage.server')
    invoke(['coverage', 'combine'])

    # print coverage report
    invoke(['coverage', 'report'])


if __name__ == '__main__':
    main()
