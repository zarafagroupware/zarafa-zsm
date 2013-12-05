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


from os.path import join
import os

from fabric.api import env

from libzsm import text
from libzsm.system import users

from fab import distro
from fab import fs


class ZcpEnv(object):
    _instance = None

    def __init__(self, distro):
        self.distro = distro

        self.my_debian_conf = '/etc/mysql/debian.cnf'
        self.zar_live_config = '/etc/zarafa'

    @classmethod
    def get(cls):
        if not cls._instance:
            dist = distro.detect_distro()
            cls._instance = cls(dist)
        return cls._instance

    @property
    def conf_templates(self):
        if fs.sh_dir_exists(self.repo_basedir):
            return join(self.repo_basedir, 'installer', 'linux')
        return '/etc/zarafa'

    @property
    def fakeroot(self):
        home = users.get_homedir()
        return join(home, env.zcp_fakeroot_dirname)

    @property
    def local_admin_users(self):
        value = 'root www-data'

        cur_user = os.getenv('LOGNAME')
        if cur_user and cur_user != 'root':
            value = value + ' {0}'.format(cur_user)

        return value

    @property
    def mysql_user(self):
        if fs.sh_file_exists(self.my_debian_conf):
            content = fs.sh_cat(self.my_debian_conf, sudo=True)
            return text.safefind('(?m)^user\s+=\s+(.*)$', content)

        elif fs.sh_dir_exists(self.zar_live_config):
            fp = join(self.zar_live_config, 'server.cfg')
            content = fs.sh_cat(fp, sudo=True)
            return text.safefind('(?m)^mysql_user\s+=\s+(.*)$', content)

    @property
    def mysql_password(self):
        if fs.sh_file_exists(self.my_debian_conf):
            content = fs.sh_cat(self.my_debian_conf, sudo=True)
            return text.safefind('(?m)^password\s+=\s+(.*)$', content)

        elif fs.sh_dir_exists(self.zar_live_config):
            fp = join(self.zar_live_config, 'server.cfg')
            content = fs.sh_cat(fp, sudo=True)
            return text.safefind('(?m)^mysql_password\s+=\s+(.*)$', content)

    @property
    def plugin_path(self):
        if fs.sh_dir_exists(self.repo_basedir):
            return join(self.repo_basedir, 'provider', 'plugins', '.libs')

    @property
    def repo_basedir(self):
        home = users.get_homedir()
        return join(home, env.zcp_repo_basedir_dirname)

    @property
    def user_plugin_config(self):
        return join(self.fakeroot, 'etc', 'zarafa', 'ldap.cfg')

    @property
    def server_ssl_ca_file(self):
        return join(self.fakeroot, 'etc', 'zarafa', 'ssl', 'demoCA', 'cacert.pem')

    @property
    def server_ssl_key_file(self):
        return join(self.fakeroot, 'etc', 'zarafa', 'ssl', 'server1.pem')

    @property
    def sslkeys_path(self):
        return join(self.fakeroot, 'etc', 'zarafa', 'sslkeys')

    @property
    def zarafa_licensed_bin(self):
        binary = 'zarafa-licensed'
        if fs.sh_dir_exists(self.repo_basedir):
            return join(self.repo_basedir, 'licensed', binary)
        return fs.sh_which(binary, sudo=True)

    @property
    def zarafa_server_bin(self):
        binary = 'zarafa-server'
        if fs.sh_dir_exists(self.repo_basedir):
            return join(self.repo_basedir, 'provider', 'server', binary)
        return fs.sh_which(binary, sudo=True)
