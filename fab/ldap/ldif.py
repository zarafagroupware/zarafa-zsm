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
import shutil

from fabric.api import env

from libzsm import text

from detect import detect_database_dn
from fab import fs
from fab.models.ldapenv import LdapEnv


def get_ldap_tmpl(template_name, context, **kwargs):
    filepath = join(
        env.ldap_template_dir, 'ldap', '{0}.in'.format(template_name))

    content = open(filepath, 'rt').read()
    content = text.patch(context, content, **kwargs)

    return content


def get_zarafa_schema():
    ldap_env = LdapEnv.get()

    with fs.mkdtemp() as d:
        shutil.copyfile(
            join(env.ldap_schema_dir, 'zarafa.schema'),
            join(d, 'zarafa.schema'))

        context = {
            'include\s+zarafa\.schema': 'include {0}'.format(join(d, 'zarafa.schema')),
            '__LDAP_ETC_PATH__': ldap_env.etc_path_orig,
        }
        conv_fp = join(d, 'schema_convert.conf')
        text.patch_file(context,
                        join(env.ldap_schema_dir, 'schema_convert.conf.in'),
                        dest=conv_fp, literal=False)

        # debian6: fails to find slaptest without abs path
        env.run('/usr/sbin/slaptest -f {0} -F {1}'.format(conv_fp, d))

        ldif_file = join(d, 'cn=config', 'cn=schema', 'cn={4}zarafa.ldif')
        context = {
            '(?m)^structuralObjectClass: .*$': '',
            '(?m)^entryUUID: .*$': '',
            '(?m)^creatorsName: .*$': '',
            '(?m)^createTimestamp: .*$': '',
            '(?m)^entryCSN: .*$': '',
            '(?m)^modifiersName: .*$': '',
            '(?m)^modifyTimestamp: .*$': '',
            '(?m)^dn: .*': 'dn: {0}'.format(env.ldap_custom_schema_dn),
            '(?m)^cn: .*': 'cn: {0}'.format(env.ldap_custom_schema_cn),
        }
        text.patch_file(context, ldif_file, dest=ldif_file, literal=False)

        content = open(ldif_file, 'rt').read()
        return content.strip()


def get_database():
    ldap_env = LdapEnv.get()

    indexes = ''
    for fname, vals in sorted(env.ldap_indexes.items()):
        indexes += 'olcDbIndex: {0} {1}\n'.format(fname, vals)

    pw_hash = env.sudo('slappasswd -s {0}'.format(env.ldap_admin_pw), capture=True)
    context = {
        '__DB_PATH__': ldap_env.database_path,
        '__DIT_DN__': env.ldap_dit_dn,
        '__DIT_ADMIN_DN__': env.ldap_admin_dn,
        '__ADMIN_PW__': pw_hash,
        '__LDAP_INDEXES__': indexes,
    }

    return get_ldap_tmpl('database.ldif', context)


def get_mod_memberof():
    return get_ldap_tmpl('mod_memberof.ldif', {})

def get_mod_memberof_config():
    pairs = [
        ('overlay',                  'memberof'),
        ('memberof-dangling',        'ignore'),
        ('memberof-refint',          'TRUE'),
        ('memberof-group-oc',        env.ldap_group_objectclass),
        ('memberof-member-ad',       'member'),
        ('memberof-memberof-ad',     'memberOf'),
    ]
    return pairs

def get_overlay_memberof():
    db_entry = detect_database_dn()
    context = {
        '__DB_RDN__': db_entry,
        '__GROUP_OBJECTCLASS__': env.ldap_group_objectclass,
    }
    return get_ldap_tmpl('overlay_memberof.ldif', context)


def get_mod_refint():
    return get_ldap_tmpl('mod_refint.ldif', {})

def get_mod_refint_config():
    atts = ' '.join(env.ldap_ref_attributes)
    pairs = [
        ('overlay',                 'refint'),
        ('refint_attributes',       atts),
    ]
    return pairs

def get_overlay_refint():
    db_entry = detect_database_dn()
    atts = ' '.join(env.ldap_ref_attributes)
    context = {
        '__DB_RDN__': db_entry,
        '__REF_ATTRIBUTES__': atts,
    }
    return get_ldap_tmpl('overlay_refint.ldif', context)


def get_base_structure():
    context = {
        '__DB_NAME__': env.ldap_database_name,
        '__DIT_DN__': env.ldap_dit_dn,
    }
    return get_ldap_tmpl('base-structure.ldif', context)


def get_slapd_conf(distro):
    ldap_env = LdapEnv(distro)

    def tabbed_line_join(data, prefix='', sort=False):
        tuples = data

        if type(data) == dict:
            tuples = data.items()

        if sort:
            tuples = sorted(tuples)

        return '\n'.join(['{0}{1:30} {2}'.format(prefix, name, props)
                          for (name, props) in tuples])

    confs = [get_mod_memberof_config(), get_mod_refint_config()]
    moduleconf = '\n\n'.join([tabbed_line_join(c) for c in confs])

    modules = '\n'.join(['moduleload\t{0}'.format(name) for name in env.ldap_modules])
    indexes = tabbed_line_join(env.ldap_indexes, prefix='index\t', sort=True)

    context = {
        '__DIT_DN__': env.ldap_dit_dn,
        '__DIT_ADMIN_DN__': env.ldap_admin_dn,
        '__ADMIN_PW__': env.ldap_admin_pw,

        '__INDEXES__': indexes,
        '__MODULES__': modules,
        '__MODULECONF__': moduleconf,

        '__ARGSFILE__': ldap_env.argsfile,
        '__ETC_LDAP__': ldap_env.etc_path,
        '__PIDFILE__': ldap_env.pidfile,
        '__VAR_LIB_LDAP__': ldap_env.database_rootdir,
    }
    return get_ldap_tmpl('slapd.conf', context)


def get_ldap_bootstrap_script(distro):
    ldap_env = LdapEnv(distro)

    context = {
        '__DIT_ADMIN_DN__': env.ldap_admin_dn,
        '__ADMIN_PW__': env.ldap_admin_pw,

        '__LDAP_GROUP__': ldap_env.ldap_group,
        '__LDAP_USER__': ldap_env.ldap_user,

        '__ETC_LDAP__': ldap_env.etc_path,
        '__ETC_LDAP_SCHEMA__': ldap_env.schema_path,
        '__ETC_LDAP_SLAPDD__': ldap_env.slapdd_path,
        '__USR_LIB_LDAP_LOCS__': ' '.join(ldap_env.module_path_locs),
        '__VAR_LIB_LDAP__': ldap_env.database_rootdir,
    }
    return get_ldap_tmpl('bootstrap-ldap.sh', context)


def get_zarafa_schema_raw():
    filepath = join(env.ldap_template_dir, 'schema', 'zarafa.schema')
    content = open(filepath, 'rt').read()
    return content.strip()
