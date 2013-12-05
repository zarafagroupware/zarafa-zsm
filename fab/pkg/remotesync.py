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

from fab import deps
from fab import fs

from packager import Packager


class RemotesyncPackager(Packager):
    def __init__(self, *args, **kwargs):
        super(RemotesyncPackager, self).__init__(*args, **kwargs)

        self.name = 'zarafa-zsm-remotesync'

        self.versiontag = '1.0'

        self.release = self.versiontag

        self.license = 'gpl'
        self.maintainer_fullname = 'Martin Matusiak'
        self.maintainer_email = 'm.matusiak@zarafa.com'
        self.python_rdeps = deps.REMOTESYNC_PYTHON_RDEPS

        self.debmeta_section = 'mail'
        self.debmeta_arch = 'all'
        self.debmeta_depends = ['python', 'python-ldap']
        self.debmeta_homepage = 'http://www.zarafa.com'
        self.debmeta_desc = 'Zarafa Server Management remote sync tool'
        self.debmeta_longdesc = 'This package provides a cmdline tool that allows synchronizing a remote Active Directory or LDAP to ZSM (unidirectional).'
        self.debmeta_changelog_msg = 'New upstream release.'

        self.rpmmeta_summary = self.debmeta_desc
        self.rpmmeta_requires = ['python', 'python-ldap']
        self.rpmmeta_group = 'Productivity/Networking/Email'
        self.rpmmeta_arch = 'noarch'
        self.rpmmeta_desc = self.debmeta_longdesc

        self.share_root = join('/usr/share', self.name)
        self.sitepkgs_root = join(self.share_root, 'site-packages')
        self.conf_root = '/etc/zarafa'

    def compile_cfg_files(self, destdir):
        conf_dir = join(self.repo_basedir, 'etc', 'zarafa')

        name = 'zsm-remotesync.cfg'
        fs.sh_copyfile(join(conf_dir, name + '.in'),
                       join(destdir, name))

        name = 'remotesync_ad.cfg'
        fs.sh_copyfile(join(conf_dir, name + '.in'),
                       join(destdir, name))

        name = 'remotesync_ldap.cfg'
        fs.sh_copyfile(join(conf_dir, name + '.in'),
                       join(destdir, name))

    def compile_makefile_extra_stmts(self, stmts):
        # add symlinks to /usr/bin
        stmts.extend([
            'mkdir -p ${DESTDIR}/usr/bin',
            'ln -s %s/remote_sync/remote_sync.py ${DESTDIR}/usr/bin/zsm-remotesync.py' % self.sitepkgs_root,
        ])

        return stmts

    def patch_src(self, destdir):
        paths = [
            self.sitepkgs_root,
            join(self.sitepkgs_root, 'remote_sync'),
        ]
        context = {
            '(?m)(EXTRA_PATHS\s*=\s*).*$':      '\g<1>{0}'.format(repr(paths)),
        }

        fp = fs.gluejoin(destdir, 'remote_sync', 'remote_sync.py')
        text.patch_file(context, fp, dest=fp, literal=False)

    def pkg_tarball(self, destdir=None):
        with fs.mkdtemp() as d:
            srcroot = join(d, self.pkgname)
            fs.sh_makedirs(srcroot)

            # Compilation
            etc_zarafa = fs.gluejoin(srcroot, self.conf_root)
            fs.sh_makedirs(etc_zarafa)
            self.compile_cfg_files(etc_zarafa)

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
