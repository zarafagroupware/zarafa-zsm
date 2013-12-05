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


import functools
import os
import sys
import time

from fabric.api import env
from fabric.api import quiet
from fabric.utils import puts

from libzsm.system import stdio
from libzsm.system import users


def sh_kill(pid, **kwargs):
    with quiet():
        return run_cmd('kill {0}'.format(pid), capture=True, **kwargs)

def sh_procalive(pid, **kwargs):
    with quiet():
        return run_cmd('ps {0}'.format(pid), capture=True, **kwargs).succeeded

def sh_kill_wait(pid, service_name, **kwargs):
    sh_kill(pid, **kwargs)

    stdio.write('Waiting for {0} to exit'.format(service_name))
    while sh_procalive(pid):
        stdio.write('.')
        time.sleep(.5)
    stdio.write('\n')


def sudo_needed(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        if not os.getuid() == 0:
            puts('You must be root to run this command, try running with sudo')
            sys.exit(1)
        return func(*args, **kwargs)
    return new_func

def hacked_sudo(cmd, context=None, *args, **kwargs):
    context = context or {}

    if not users.is_root():
        extra = ' '.join(['{0}={1}'.format(k, v) for (k, v) in context.items()])
        cmd = 'sudo {0} {1}'.format(extra, cmd)

    return env.run(cmd, *args, **kwargs)

def run_cmd(cmd, sudo=False, capture=True):
    if sudo:
        return env.sudo(cmd, capture=capture)
    else:
        return env.run(cmd, capture=capture)

class setenv(object):
    '''Temporarily set an env var.'''

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __enter__(self):
        self.orig_value = os.getenv(self.key)

        value = self.value
        if self.key.endswith('PATH') and self.orig_value:
            value = '{0}:{1}'.format(value, self.orig_value)

        os.environ[self.key] = value

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.orig_value:
            os.environ[self.key] = self.orig_value

    def run(self, *args, **kwargs):
        return env.run(*args, **kwargs)

    def sudo(self, *args, **kwargs):
        '''Pass the custom env var to sudo.'''
        return env.sudo(context={self.key: self.value}, *args, **kwargs)
