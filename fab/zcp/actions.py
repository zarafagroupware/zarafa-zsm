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


from os.path import dirname
from os.path import join
import os

from fabric.api import env
from fabric.api import warn_only
from fabric.utils import puts
from fabric.utils import warn

from libzsm import text

from fab import fs
from fab import proc
from fab.models.zcpenv import ZcpEnv


def drop_mysql_database():
    zcpenv = ZcpEnv.get()

    with warn_only():
        env.run('mysqladmin -u {0} -p{1} drop {2} -f'.format(
            zcpenv.mysql_user,
            zcpenv.mysql_password,
            env.zcp_mysql_dbname,
        ))


def patch_config():
    zcpenv = ZcpEnv.get()

    ## Create fakeroot dir structure

    fs.sh_makedirs(join(zcpenv.fakeroot, 'etc', 'zarafa', 'license'))
    fs.sh_makedirs(join(zcpenv.fakeroot, 'etc', 'zarafa', 'ssl'))
    fs.sh_makedirs(join(zcpenv.fakeroot, 'etc', 'zarafa', 'sslkeys'))
    fs.sh_makedirs(join(zcpenv.fakeroot, 'var', 'run'))
    fs.sh_makedirs(join(zcpenv.fakeroot, 'var', 'log', 'zarafa'))


    ## Patch server.cfg

    filepath = join(zcpenv.conf_templates, 'server.cfg')
    fp = join(zcpenv.fakeroot, 'etc', 'zarafa', 'server.cfg')

    # 1) regex rewrites
    context = {
        '/etc/': join(zcpenv.fakeroot, 'etc/'),
        '/var/': join(zcpenv.fakeroot, 'var/'),
    }
    text.patch_file(context, filepath, dest=fp, literal=True)

    # 2) config patching
    context = env.zcp_server_cfg
    context.update({
        'local_admin_users': zcpenv.local_admin_users,
        'mysql_user': zcpenv.mysql_user,
        'mysql_password': zcpenv.mysql_password,
        'plugin_path': zcpenv.plugin_path,
        'user_plugin_config': zcpenv.user_plugin_config,

        # ssl settings
        'server_ssl_ca_file': zcpenv.server_ssl_ca_file,
        'server_ssl_key_file': zcpenv.server_ssl_key_file,
        'sslkeys_path': zcpenv.sslkeys_path,
    })
    text.patch_config_file(env.zcp_server_cfg, fp, dest=fp)


    ## Patch ldap.cfg

    filepath = join(zcpenv.conf_templates, 'ldapms.openldap.cfg')
    fp = join(zcpenv.fakeroot, 'etc', 'zarafa', 'ldap.cfg')

    # 1) regex rewrites
    context = {
        '/etc/': join(zcpenv.fakeroot, 'etc/'),
    }
    text.patch_file(context, filepath, dest=fp, literal=True)

    # 2) config patching
    text.patch_config_file(env.zcp_ldap_cfg, fp, dest=fp)


    ## Deploy ldap.propmap.cfg

    src = join(zcpenv.conf_templates, 'ldap.propmap.cfg')
    dest = join(zcpenv.fakeroot, 'etc', 'zarafa', 'ldap.propmap.cfg')
    fs.sh_copyfile(src, dest)


    ## Patch licensed.cfg

    filepath = join(zcpenv.conf_templates, 'licensed.cfg')
    fp = join(zcpenv.fakeroot, 'etc', 'zarafa', 'licensed.cfg')

    # regex rewrites
    context = {
        '/etc/': join(zcpenv.fakeroot, 'etc/'),
        '/var/': join(zcpenv.fakeroot, 'var/'),
    }
    text.patch_file(context, filepath, dest=fp, literal=True)


    ## Deploy license file

    src = join('etc', 'zarafa', 'license', 'base')
    dest = join(zcpenv.fakeroot, 'etc', 'zarafa', 'license', 'base')
    fs.sh_copyfile(src, dest)


    ## Deploy ssl config

    src = join('etc', 'zarafa', 'ssl')
    dest = join(zcpenv.fakeroot, 'etc', 'zarafa')
    fs.sh_rmtree(join(dest, 'ssl'))
    fs.sh_copytree(src, dest)

    src = join('etc', 'zarafa', 'sslkeys')
    dest = join(zcpenv.fakeroot, 'etc', 'zarafa')
    fs.sh_rmtree(join(dest, 'sslkeys'))
    fs.sh_copytree(src, dest)


def start_services():
    zcpenv = ZcpEnv.get()

    cfg = join(zcpenv.fakeroot, 'etc', 'zarafa', 'licensed.cfg')
    env.run('{0} -c {1}'.format(zcpenv.zarafa_licensed_bin, cfg))

    cfg = join(zcpenv.fakeroot, 'etc', 'zarafa', 'server.cfg')
    env.sudo('{0} -c {1}'.format(zcpenv.zarafa_server_bin, cfg))


def stop_services():
    zcpenv = ZcpEnv.get()

    server_pidfile = join(zcpenv.fakeroot, 'var', 'run', 'zarafa-server.pid')
    licensed_pidfile = join(zcpenv.fakeroot, 'var', 'run', 'zarafa-licensed.pid')

    server_pid = fs.sh_cat(server_pidfile, sudo=True)
    licensed_pid = fs.sh_cat(licensed_pidfile)

    if licensed_pid:
        proc.sh_kill(licensed_pid)

    proc.sh_kill_wait(server_pid, 'zarafa-server', sudo=True)


def setup_local_zcp():
    zcpenv = ZcpEnv.get()

    puts('Setting up MAPI_CONFIG_PATH')
    sys_mapi_config_path = '/etc/mapi'
    if fs.sh_dir_exists(sys_mapi_config_path):
        warn('{0} directory exists, cannot set up symlink'.format(
            sys_mapi_config_path))

    else:
        local_mapi_config_path = join(
            zcpenv.repo_basedir, 'provider', 'client')
        fs.sh_ln(local_mapi_config_path, sys_mapi_config_path,
                 sudo=True)

    puts('Setting up LD_LIBRARY_PATH')
    ld_conf = '/etc/ld.so.conf.d'
    with fs.mkstemp() as fp:
        dest = join(ld_conf, 'zarafa.conf')

        paths = [
            join(zcpenv.repo_basedir, 'provider', 'client', '.libs'),
        ]
        paths = '\n'.join(paths) + '\n'
        open(fp, 'wt').write(paths)

        fs.sh_copyfile(fp, dest, sudo=True)
        fs.sh_chmod(dest, 644, sudo=True)

        env.sudo('ldconfig')

    puts('Setting up PYTHONPATH')
    pyhome = dirname(os.__file__)
    pkg_dir_dir = join(pyhome, 'dist-packages')
    with fs.mkstemp() as fp:
        dest = join(pkg_dir_dir, 'MAPI.pth')

        paths = [
            join(zcpenv.repo_basedir, 'swig', 'python'),
            join(zcpenv.repo_basedir, 'swig', 'python', '.libs'),
        ]
        paths = '\n'.join(paths) + '\n'
        open(fp, 'wt').write(paths)

        fs.sh_copyfile(fp, dest, sudo=True)
        fs.sh_chmod(dest, 644, sudo=True)

    puts('Setting up ZARAFA_SOCKET')
    src = join(zcpenv.fakeroot, 'var', 'run', 'zarafa')
    if not os.path.exists(src):
        warn('Path does not exist: {0}'.format(src))

    else:
        dest = '/var/run/zarafa'
        if fs.sh_exists(dest):
            fs.sh_rm(dest, sudo=True)
        fs.sh_ln(src, dest, sudo=True)

    puts('Setting up ssl client cert')
    src = join('etc', 'zarafa', 'ssl', 'client.pem')
    destdir = '/etc/zarafa/sslkeys'
    dest = join(destdir, 'client.pem')

    if not fs.sh_exists(dest):
        fs.sh_makedirs(destdir, sudo=True)
        fs.sh_copyfile(src, dest, sudo=True)
