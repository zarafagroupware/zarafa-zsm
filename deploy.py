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



import sys

EXTRA_PATHS = []

for p in EXTRA_PATHS:
    sys.path.append(p)


from optparse import OptionParser
from os.path import join
import os
import shutil

from libzsm import text
from libzsm.system import stdio
from libzsm.system import users


def run_cmd(args):
    args = ' '.join(args)
    os.system(args)


class Deployer(object):
    def __init__(self):
        self.detect_apache_env()

        self.ldapconf_boostrap_ldap = '/usr/share/zarafa-zsm-ldapconf/bootstrap-ldap.sh'
        self.zsm_config_source = '/usr/share/zarafa-zsm-server/config'

        self.etc_zarafa_root = '/etc/zarafa'
        self.zarafa_server_cfg = join(self.etc_zarafa_root, 'server.cfg')

        self.zarafa_ldap_cfg_tmpl = '/etc/zarafa/{0}.zsm.cfg'

    ## Apache

    def detect_apache_env(self):
        if os.path.exists('/etc/apache2'):
            self.apache_user = 'www-data'
            self.apache_initscript = '/etc/init.d/apache2'
            self.apache_default_site_conf = '/etc/apache2/sites-enabled/000-default'

        elif os.path.exists('/etc/httpd'):
            self.apache_user = 'apache'
            self.apache_initscript = '/etc/init.d/httpd'
            self.apache_default_site_conf = '/etc/httpd/conf.d/welcome.conf'

    def remove_default_apache_site(self):
        if os.path.exists(self.apache_default_site_conf):
            os.unlink(self.apache_default_site_conf)

    def restart_apache(self):
        run_cmd([self.apache_initscript, 'restart'])

    ## LDAP

    def bootstrap_ldap(self):
        run_cmd([self.ldapconf_boostrap_ldap])

    ## Zarafa

    def switch_zarafa_server_plugin(self):
        content = open(self.zarafa_server_cfg, 'rt').read()
        plugin = text.safefind('(?m)^user_plugin\s*=\s*(.*)$', content)

        if plugin not in ['ldap', 'ldapms']:
            stdio.die('Invalid zarafa user plugin found: {0}'.format(plugin))

        zarafa_ldap_cfg = self.zarafa_ldap_cfg_tmpl.format(plugin)

        if not os.path.isfile(zarafa_ldap_cfg):
            stdio.die('Ldap config not found: {0}'.format(zarafa_ldap_cfg))

        context = {
            'user_plugin_config': zarafa_ldap_cfg,
        }
        text.patch_config_file(context, self.zarafa_server_cfg,
                               dest=self.zarafa_server_cfg)

    def fixup_zarafa_server_cfg(self):
        context = {
            'enable_distributed_zarafa': 'false',
            'enable_hosted_zarafa': 'true',
            'loginname_format': '%u@%c',
            #'storename_format': '%u@%c',
            'storename_format': '%f',
            'user_plugin': 'ldap',  # NOTE or ldapms?
        }
        text.patch_config_file(context, self.zarafa_server_cfg,
                               dest=self.zarafa_server_cfg)

    def add_apache_user_to_zarafa_server_cfg(self):
        us = ['root', self.apache_user]
        context = {
            'local_admin_users': ' '.join(us),
        }
        text.patch_config_file(context, self.zarafa_server_cfg,
                               dest=self.zarafa_server_cfg)

    def restart_zarafa_server(self):
        run_cmd(['/etc/init.d/zarafa-server', 'restart'])

    ## ZSM

    def deploy_zsm_config_files(self):
        for fn in ['ldap.zsm.cfg', 'ldapms.zsm.cfg']:
            shutil.copy(join(self.zsm_config_source, fn),
                        join(self.etc_zarafa_root, fn))

    def load_zsm_ldap_base(self):
        run_cmd(['zsm-manage.py', 'load_ldap_base'])
        run_cmd(['zsm-manage.py', 'sync_users'])

    def load_zsm_ldap_fixtures(self):
        run_cmd(['zsm-manage.py', 'load_demo_data'])


    def deploy(self):
        self.bootstrap_ldap()

        self.deploy_zsm_config_files()
        self.fixup_zarafa_server_cfg()
        self.switch_zarafa_server_plugin()
        self.add_apache_user_to_zarafa_server_cfg()
        self.restart_zarafa_server()

        self.remove_default_apache_site()
        self.restart_apache()

        self.load_zsm_ldap_base()
        self.load_zsm_ldap_fixtures()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--single-server', dest='single_server', action='store_true',
                      help='Deploy LDAP, Zarafa and ZSM on a single server.')
    options, args = parser.parse_args()


    if not users.is_root():
        stdio.writeln("Run me as root")
        sys.exit(2)

    if options.single_server:
        deployer = Deployer()
        deployer.deploy()

    else:
        parser.print_help()
        sys.exit(1)
