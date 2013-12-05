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

from libzsm import archive
from libzsm import text
from libzsm.system import stdio

from fab import apache
from fab import deps
from fab import fs
from fab import proc
from fab.ldap import ldif
from fab.proc import run_cmd

from packager import Packager


__all__ = ['ServerPackager']  # to avoid exporting tasks from fab.apache


class ServerPackager(Packager):
    def __init__(self, *args, **kwargs):
        super(ServerPackager, self).__init__(*args, **kwargs)

        self.name = 'zarafa-zsm-server'

        self.versiontag = '1.0'

        self.release = self.versiontag

        self.license = 'gpl'
        self.maintainer_fullname = 'Martin Matusiak'
        self.maintainer_email = 'm.matusiak@zarafa.com'
        self.python_rdeps = deps.WEBSERVICE_PYTHON_RDEPS

        self.debmeta_section = 'mail'
        self.debmeta_arch = 'all'
        self.debmeta_depends = ['python', 'python-ldap', 'apache2', 'libapache2-mod-wsgi']
        self.debmeta_homepage = 'http://www.zarafa.com'
        self.debmeta_desc = 'Zarafa Server Management Webservice'
        self.debmeta_longdesc = 'This package provides a webservice which serves as an API frontend to OpenLDAP and the Zarafa Collaboration Platform.'
        self.debmeta_changelog_msg = 'New upstream release.'

        self.rpmmeta_summary = self.debmeta_desc
        self.rpmmeta_requires = ['python', 'python-ldap', 'httpd', 'mod_wsgi']
        self.rpmmeta_group = 'Productivity/Networking/Email'
        self.rpmmeta_arch = 'noarch'
        self.rpmmeta_desc = self.debmeta_longdesc

        self.share_root = join('/usr/share', self.name)
        self.usr_share_conf_root = join(self.share_root, 'config')
        self.sitepkgs_root = join(self.share_root, 'site-packages')
        self.conf_root = '/etc/zarafa'
        self.apache_confd_path = '/etc/apache2/conf.d'
        self.apache_logdir = '/var/log/apache2'

        if self.flavor == 'rpm':
            self.apache_confd_path = '/etc/httpd/conf.d'
            self.apache_logdir = '/var/log/httpd'

    def compile_apache_vhost(self, destdir):
        content = apache.get_vhost(
            logdir=self.apache_logdir,
            is_rpmdistro=self.flavor == 'rpm',
            repo_root=self.sitepkgs_root,
        )
        fp = join(destdir, 'zarafa-zsm.conf')
        open(fp, 'wt').write(content)

    def compile_cfg_files(self, etc_destdir, usr_share_destdir):
        conf_dir = join(self.repo_basedir, 'etc', 'zarafa')

        name = 'zsm-server.cfg'
        fs.sh_copyfile(join(conf_dir, name + '.in'),
                       join(etc_destdir, name))

        name = 'ldap.zsm.cfg'
        fs.sh_copyfile(join(conf_dir, name + '.in'),
                       join(usr_share_destdir, name))

        name = 'ldapms.zsm.cfg'
        fs.sh_copyfile(join(conf_dir, name + '.in'),
                       join(usr_share_destdir, name))

    def compile_ldif_templates(self, destdir):
        content = []
        content.append(ldif.get_zarafa_schema())
        content.append(ldif.get_database())
        content.append(ldif.get_mod_memberof())
        content.append(ldif.get_overlay_memberof())
        content.append(ldif.get_mod_refint())
        content.append(ldif.get_overlay_refint())
        content = '\n\n'.join(content) + '\n'

        fp = join(destdir, 'ldap-config.ldif')
        open(fp, 'wt').write(content)

        content = []
        content.append(ldif.get_base_structure())
        content = '\n\n'.join(content) + '\n'

        fp = join(destdir, 'ldap-base-structure.ldif')
        open(fp, 'wt').write(content)

        conf_dir = join(self.repo_basedir, 'etc', 'ldap')
        fs.sh_copyfile(join(conf_dir, 'bootstrap-ldap.sh'),
                       join(destdir, 'bootstrap-ldap.sh'))

    def compile_makefile_extra_stmts(self, stmts):
        # add symlinks to /usr/bin
        stmts.extend([
            'mkdir -p ${DESTDIR}/usr/bin',
            'ln -s %s/webservice/manage.py ${DESTDIR}/usr/bin/zsm-manage.py' % self.sitepkgs_root,
        ])

        return stmts

    def patch_src(self, destdir):
        paths = [
            self.sitepkgs_root,
        ]

        context = {
            '(?m)(EXTRA_PATHS\s*=\s*).*$':      '\g<1>{0}'.format(repr(paths)),
        }

        fp = fs.gluejoin(destdir, 'deploy.py')
        text.patch_file(context, fp, dest=fp, literal=False)

        context.update({
            '(?m)(PERFORM_RELOAD\s*=\s*).*$':   '\g<1>False',
            '(?m)(SETTINGS_MODULE\s*=\s*).*$':  '\g<1>{0}'.format(repr('zsm.settings')),
        })

        fp = fs.gluejoin(destdir, 'webservice', 'manage.py')
        text.patch_file(context, fp, dest=fp, literal=False)

    def include_deps_post_hook(self, destdir, venv):
        # Collect static files
        py = join(venv.location, 'bin', 'python')
        manage_py = join(destdir, 'webservice', 'manage.py')

        with proc.setenv('PYTHONPATH', destdir):
            output = run_cmd('{0} {1} collectstatic --noinput'.format(py, manage_py))
            output = run_cmd('{0} {1} compile_pygments_css'.format(py, manage_py))
            stdio.write(output)

    def pkg_tarball(self, destdir=None):
        with fs.mkdtemp() as d:
            srcroot = join(d, self.pkgname)
            fs.sh_makedirs(srcroot)

            # Compilation
            etc_apache = fs.gluejoin(srcroot, self.apache_confd_path)
            fs.sh_makedirs(etc_apache)
            self.compile_apache_vhost(etc_apache)

            etc_zarafa = fs.gluejoin(srcroot, self.conf_root)
            usr_share_conf = fs.gluejoin(srcroot, self.usr_share_conf_root)
            fs.sh_makedirs(etc_zarafa)
            fs.sh_makedirs(usr_share_conf)
            self.compile_cfg_files(etc_zarafa, usr_share_conf)

            # Include source
            share = fs.gluejoin(srcroot, self.sitepkgs_root)

            self.include_python_packages(self.repo_basedir, share)

            self.patch_src(share)

            # Include dependencies
            self.include_deps(share)

            # Generate makefile
            self.compile_makefile(srcroot)

            destdir = destdir or d

            targz_fp = join(destdir, self.targz_name)
            with archive.tarfile(targz_fp, 'w:gz') as tar:
                tar.add(d, arcname='')

            return targz_fp
