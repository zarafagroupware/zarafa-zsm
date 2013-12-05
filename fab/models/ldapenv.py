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
import random
import socket

from fabric.api import env

from fab import distro
from fab import fs
from fab.models.distromodel import PkgMan


class LdapEnv(object):
    _instance = None

    def __init__(self, distro):
        if distro.pkgman == PkgMan.Apt:
            self.ldap_group = 'openldap'
            self.ldap_user = 'openldap'
            self.etc_path_orig = '/etc/ldap'
            self.argsfile = '/var/run/slapd/slapd.args'
            self.pidfile = '/var/run/slapd/slapd.pid'
            self.module_path_locs = [
                '/usr/lib/ldap',
                '/usr/lib64/ldap',
            ]

        elif distro.pkgman == PkgMan.Yum:
            self.ldap_group = 'ldap'
            self.ldap_user = 'ldap'
            self.etc_path_orig = '/etc/openldap'
            self.argsfile = '/var/run/openldap/slapd.args'
            self.pidfile = '/var/run/openldap/slapd.pid'
            self.module_path_locs = [
                '/usr/lib/openldap',
                '/usr/lib64/openldap',
            ]

        self.database_rootdir_orig = '/var/lib/ldap'  # debian/rhel std location

        self.is_tmp_daemon = False

    @classmethod
    def get(cls):
        if getattr(env, 'ldap_env', None):
            return env.ldap_env

        if not cls._instance:
            dist = distro.detect_distro()
            cls._instance = cls(dist)
        return cls._instance

    @property
    def cn_config_path(self):
        return join(self.slapdd_path, 'cn=config')

    @property
    def database_path(self):
        return join(self.database_rootdir, env.ldap_database_name)

    @property
    def database_rootdir(self):
        return self.database_rootdir_orig

    @property
    def etc_path(self):
        return self.etc_path_orig

    def get_pid(self):
        content = fs.sh_cat(self.pidfile, sudo=True)
        content = content.strip()
        if content:
            return int(content)

    @property
    def host(self):
        return '127.0.0.1'

    @property
    def port(self):
        if self.is_tmp_daemon:
            s = socket.socket()
            while True:
                try:
                    i = random.randint(1025, 65500)
                    s.bind((self.host, i))
                    s.close()
                    return i
                except:
                    pass

        return 389

    @property
    def schema_path(self):
        return join(self.etc_path, 'schema')

    @property
    def slapd_args(self):
        args = [
            '/usr/sbin/slapd',
            '-h', '"ldap://{0}:{1}/ ldapi:///"'.format(self.host, self.port),
            '-g', self.ldap_group,
            '-u', self.ldap_user,
            '-F', self.slapdd_path,
        ]
        return args

    @property
    def slapdd_path(self):
        return join(self.etc_path, 'slapd.d')
