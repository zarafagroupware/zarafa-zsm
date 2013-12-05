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
import os

from fabric.api import env

from libzsm.system import users

from fab import proc


def sh_apt_install(pkgs):
    pkgs = ' '.join(pkgs)

    with proc.setenv('DEBIAN_FRONTEND', 'noninteractive') as _env:
        _env.sudo('apt-get -y install {0}'.format(pkgs))


def sh_pip_install(pkgs, cmd_path='pip', sudo=True):
    args = [
        cmd_path,
        'install',
        #'--use-mirrors',  # unavailable on deb6 pip
    ]

    if env.pypi_package_download_cache:
        cache_dir = env.pypi_package_download_cache.format(
            username=users.get_username()
        )
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        extra = ['--download-cache={0}'.format(cache_dir)]
        args.extend(extra)

    pkgs = list(set(pkgs))  # remove duplicate packages, pip complains

    args.extend(pkgs)
    args = ' '.join(args)

    if sudo:
        env.sudo(args)
    else:
        env.run(args)


def sh_yum_install(pkgs):
    rest_pkgs = []
    for pkg in pkgs:
        if re.match('''^(['"]).*(['"])$''', pkg):
            env.sudo('yum -y groupinstall {0}'.format(pkg))
        else:
            rest_pkgs.append(pkg)

    if rest_pkgs:
        pkgs = ' '.join(rest_pkgs)
        env.sudo('yum -y install {0}'.format(pkgs))
