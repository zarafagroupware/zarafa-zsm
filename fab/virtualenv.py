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
import shutil
import sys

from fabric.api import lcd
from fabric.api import quiet

from fab import package_manager
from fab.proc import run_cmd


def sh_mkenv(cwd, name, **kwargs):
    with lcd(cwd):
        with quiet():
            return run_cmd('virtualenv {0}'.format(name), capture=True, **kwargs)


class venv(object):
    def __init__(self, cwd, name):
        self.cwd = cwd
        self.name = name

    @property
    def location(self):
        return os.path.join(self.cwd, self.name)

    @property
    def pkgs_location(self):
        py = 'python{0}'.format(sys.version[:3])
        return os.path.join(self.location, 'lib', py, 'site-packages')

    def __enter__(self):
        sh_mkenv(self.cwd, self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.isdir(self.location):
            shutil.rmtree(self.location)

    def install_pkgs(self, pkgnames):
        assert type(pkgnames) == list

        pip = os.path.join(self.location, 'bin', 'pip')
        package_manager.sh_pip_install(pkgnames, cmd_path=pip, sudo=False)
