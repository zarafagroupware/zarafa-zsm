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
import fnmatch
import os

from fabric.api import env
from fabric.api import warn_only

from libzsm import text
from libzsm.system.stdio import puth
from libzsm.system.stdio import putw

from fab import fs
from fab import proc
from fab.models.ldapenv import LdapEnv
import ldif


def start():
    ldap_env = LdapEnv.get()

    if ldap_env.is_tmp_daemon:
        args = ldap_env.slapd_args
        args = ' '.join(args)
        with warn_only():
            proc.run_cmd(args, sudo=True)
    else:
        env.sudo('service slapd start')

def stop():
    ldap_env = LdapEnv.get()

    if ldap_env.is_tmp_daemon:
        pid = ldap_env.get_pid()
        if pid:
            proc.sh_kill_wait(pid, 'slapd', sudo=True)
    else:
        env.sudo('service slapd stop')

def restart():
    stop()
    start()


def create_database():
    ldap_env = LdapEnv.get()

    if not fs.sh_dir_exists(ldap_env.database_path, sudo=True):
        puth('Creating database directory {0}'.format(ldap_env.database_path))
        fs.sh_makedirs(ldap_env.database_path,
                       user=ldap_env.ldap_user,
                       group=ldap_env.ldap_group,
                       sudo=True)

    with fs.mkstemp() as fp:
        content = ldif.get_database()
        open(fp, 'wt').write(content)

        puth('Creating database config for {0}'.format(env.ldap_database_name))
        env.sudo('ldapadd -Y EXTERNAL -H ldapi:/// -f {0}'.format(fp))


def drop_database():
    ldap_env = LdapEnv.get()

    files = fs.sh_listdir(ldap_env.cn_config_path, sudo=True)
    files = fnmatch.filter(files, 'olcDatabase={*}hdb.ldif')

    filepath = None
    for f in files:

        fp = join(ldap_env.cn_config_path, f)
        content = fs.sh_cat(fp, sudo=True)
        if text.safefind('(?m)^olcSuffix: ' + env.ldap_dit_dn, content):
            filepath = fp

    if not filepath:
        putw('Failed to detect database: {0}'.format(env.ldap_dit_dn))
    else:
        puth('Removing database config {0}'.format(filepath))
        fs.sh_rm(filepath, sudo=True)

        root, _ = os.path.splitext(filepath)
        if fs.sh_dir_exists(root, sudo=True):
            puth('Removing database config subdir {0}'.format(root))
            fs.sh_rmtree(root, sudo=True)


def delete_database_storage():
    ldap_env = LdapEnv.get()

    if fs.sh_dir_exists(ldap_env.database_path, sudo=True):
        puth('Deleting database directory {0}'.format(ldap_env.database_path))
        fs.sh_rmtree(ldap_env.database_path, sudo=True)


def load_schema():
    puth('Loading schema')
    with fs.mkstemp() as fp:
        content = ldif.get_zarafa_schema()
        open(fp, 'wt').write(content)
        env.sudo('ldapadd -Y EXTERNAL -H ldapi:/// -f {0}'.format(fp))


def unload_schema():
    ldap_env = LdapEnv.get()

    schema_dir = join(ldap_env.cn_config_path, 'cn=schema')
    files = fs.sh_listdir(schema_dir, sudo=True)
    files = fnmatch.filter(files, 'cn={*}%s.ldif' % env.ldap_custom_schema_cn)

    if not files:
        putw('Failed to detect schema: {0}'.format(env.ldap_custom_schema_cn))
    else:
        filepath = join(schema_dir, files[0])
        puth('Removing schema {0}'.format(filepath))
        fs.sh_rm(filepath, sudo=True)


def load_modules():
    for name in env.ldap_modules:
        funcname = 'load_module_{0}'.format(name)
        try:
            puth('Loading module {0}'.format(name))
            func = eval(funcname)
            func()
        except NameError:
            pass


def load_module_memberof():
    with fs.mkstemp() as fp:
        content = ldif.get_mod_memberof()
        open(fp, 'wt').write(content)
        env.sudo('ldapadd -Y EXTERNAL -H ldapi:/// -f {0}'.format(fp))

    with fs.mkstemp() as fp:
        content = ldif.get_overlay_memberof()
        open(fp, 'wt').write(content)
        env.sudo('ldapadd -Y EXTERNAL -H ldapi:/// -f {0}'.format(fp))


def load_module_refint():
    with fs.mkstemp() as fp:
        content = ldif.get_mod_refint()
        open(fp, 'wt').write(content)
        env.sudo('ldapadd -Y EXTERNAL -H ldapi:/// -f {0}'.format(fp))

    with fs.mkstemp() as fp:
        content = ldif.get_overlay_refint()
        open(fp, 'wt').write(content)
        env.sudo('ldapadd -Y EXTERNAL -H ldapi:/// -f {0}'.format(fp))


def unload_modules():
    ldap_env = LdapEnv.get()

    for name in env.ldap_modules:
        filepath = None

        files = fs.sh_listdir(ldap_env.cn_config_path, sudo=True)
        files = fnmatch.filter(files, 'cn=module{*}.ldif')
        for f in files:
            fp = join(ldap_env.cn_config_path, f)
            if fs.sh_file_exists(fp, sudo=True):
                content = fs.sh_cat(fp, sudo=True)
                if text.safefind('(?m)^olcModuleLoad: {[0-9]+}' + name, content):
                    filepath = fp

        if not filepath:
            putw('Failed to detect loaded module: {0}'.format(name))
        else:
            puth('Removing module {0}'.format(name))
            fs.sh_rm(filepath, sudo=True)


def populate_database():
    puth('Populating database')
    with fs.mkstemp() as fp:
        content = ldif.get_base_structure()
        open(fp, 'wt').write(content)

        env.sudo('ldapadd -x -D {0} -w {1} -f {2}'.format(
            env.ldap_admin_dn,
            env.ldap_admin_pw,
            fp))
