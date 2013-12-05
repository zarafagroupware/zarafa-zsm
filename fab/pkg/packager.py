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
import fnmatch
import os
import re
import shutil

from fabric.api import lcd
from fabric.api import warn_only

from libzsm import archive
from libzsm import templates
from libzsm import text

from fab import fs
from fab import scm
from fab import virtualenv
from fab.proc import run_cmd
import manifest


class Packager(object):
    def __init__(self, flavor=None):
        self.flavor = flavor

        self.buildnum = scm.get_commit_id()

        self.tmpl_env = self.get_tmpl_env()

    @property
    def product_dir(self):
        path = join(self.repo_basedir, 'dist')
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    @property
    def repo_basedir(self):
        return dirname(dirname(dirname(__file__)))

    @property
    def pkgname(self):
        return '{0}-{1}'.format(self.name, self.release)

    @property
    def targz_name(self):
        return '{0}.tar.gz'.format(self.pkgname)

    def get_tmpl_env(self):
        d = join(self.repo_basedir, 'etc')
        return templates.get_env(d)

    def compile_makefile(self, srcroot):
        tmpl = self.tmpl_env.get_template('packaging/Makefile.in')

        stmts = []
        for r, dirs, files in os.walk(srcroot):
            relroot = re.sub(re.escape(srcroot), '', r)
            relroot = '/' if relroot == '' else relroot

            if relroot != '/':
                stm = 'mkdir -p ${DESTDIR}%s' % relroot
                stmts.append(stm)

            for f in files:
                fsrc = fs.gluejoin(srcroot, relroot, f)
                f = fs.gluejoin(relroot, f)

                mode = 755 if os.access(fsrc, os.X_OK) else 644

                stm = 'install -m%s %s ${DESTDIR}%s' % (mode, f[1:], f)
                stmts.append(stm)

        stmts = self.compile_makefile_extra_stmts(stmts)

        stmts = '\n'.join(['\t' + stm for stm in stmts]) + '\n'

        content = tmpl.render(
            statements=stmts,
        )
        fp = join(srcroot, 'Makefile')
        open(fp, 'wt').write(content)

    def compile_makefile_extra_stmts(self, stmts):
        return stmts

    def include_deps(self, destdir=None):
        with fs.mkdtemp() as workon_tmp:
            with virtualenv.venv(workon_tmp, 'pkgtmp') as venv:
                venv.install_pkgs(self.python_rdeps)
                self.include_python_packages(venv.pkgs_location, destdir)

                # allow running more commands while we have the virtualenv
                self.include_deps_post_hook(destdir, venv)

    def include_deps_post_hook(self, destdir, venv):
        pass

    def include_python_packages(self, srcdir, destdir):
        # scan tree
        files = fs.listdir_recursive(srcdir)

        # filter with manifest
        manifest_fp = join(self.repo_basedir, 'etc', 'packaging', '{0}.manifest'.format(self.name))
        files = manifest.apply_filter(manifest_fp, files)

        # copy to destination
        fs.merge_fileset(files, srcdir, destdir)

    def patch_src(self, destdir):
        pass

    def pkg_tarball(self, destdir=None):
        raise NotImplementedError

    def do_pkg_deb(self, destdir=None, targz_fp=None):
        if not targz_fp:
            targz_fp = self.pkg_tarball(destdir=destdir)

        # untar tarball
        with archive.tarfile(targz_fp, 'r:gz') as tar:
            tar.extractall(destdir)

        # clone dh_make
        dh_make_src = fs.sh_which('dh_make')
        dh_make = join(destdir, 'dh_make')
        shutil.copy2(dh_make_src, dh_make)

        # get rid of dh_make interactive prompt
        context = {
            '(?m)^.*my [$]dummy = <STDIN>.*$': '',
        }
        text.patch_file(context, dh_make, dest=dh_make, literal=False)

        pkgloc = join(destdir, self.pkgname)
        with lcd(pkgloc):
            # debianize
            os.environ['DEBFULLNAME'] = self.maintainer_fullname
            os.environ['DEBEMAIL'] = self.maintainer_email
            run_cmd('{0} -i -c {1} -e {2} -f {3}'.format(
                dh_make, self.license, self.maintainer_email,
                '../{0}'.format(self.targz_name)))

            # patch control file
            control_fp = join(pkgloc, 'debian', 'control')
            context = {
                '(?m)^(Section:).*$': '\g<1> {0}'.format(self.debmeta_section),
                '(?m)^(Homepage:).*$': '\g<1> {0}'.format(self.debmeta_homepage),
                '(?m)^(Depends:.*)$': '\g<1>, {0}'.format(', '.join(self.debmeta_depends)),
                '(?m)^(Description:).*$': '\g<1> {0}'.format(self.debmeta_desc),
                '(?m)^ [<]insert long description.*$': ' {0}'.format(self.debmeta_longdesc),
            }
            text.patch_file(context, control_fp, dest=control_fp, literal=False)

            # patch changelog file
            changelog_fp = join(pkgloc, 'debian', 'changelog')
            context = {
                '(?m)^.*[*] Initial release.*$': '  * {0}'.format(self.debmeta_changelog_msg),
                '(?m)^.*({0} )[(]([0-9._-]+)[)](.*)$'.format(self.name): '\g<1>({0}-{1})\g<3>'.format(self.release, self.buildnum),
            }
            text.patch_file(context, changelog_fp, dest=changelog_fp, literal=False)

            # replace copyright file
            copyright_fp = join(pkgloc, 'debian', 'copyright')
            shutil.copyfile(
                join(self.repo_basedir, 'etc', 'packaging',
                     '{0}.license'.format(self.name)),
                copyright_fp,
            )

            debian_dir = join(pkgloc, 'debian')
            fs.rm(debian_dir, 'README.Debian')
            fs.rm(debian_dir, '*.ex')
            fs.rm(debian_dir, '*.EX')

            # build the package
            with warn_only():
                run_cmd('dpkg-buildpackage -rfakeroot -uc -us')  # omit pgp signing

    def pkg_deb(self):
        with fs.mkdtemp() as d:
            self.do_pkg_deb(destdir=d)

            files = os.listdir(d)
            files = fnmatch.filter(files, '*.deb')
            shutil.copy(join(d, files[0]), self.product_dir)

    def do_pkg_rpm(self, destdir=None, targz_fp=None):
        if not targz_fp:
            targz_fp = self.pkg_tarball(destdir=destdir)

        # untar tarball
        with archive.tarfile(targz_fp, 'r:gz') as tar:
            tar.extractall(destdir)

        # create skeleton for rpmbuild
        rpmbuild_dir = join(destdir, 'rpmbuild')
        for d in ['RPMS', 'SOURCES', 'SPECS', 'SRPMS', 'BUILD']:
            d = join(rpmbuild_dir, d)
            os.makedirs(d)

        # copy tarball to the right place
        shutil.copyfile(targz_fp,
                        join(rpmbuild_dir, 'SOURCES', self.targz_name))

        # clone spec file
        specfile = '{0}.spec'.format(self.name)
        specfile_fp = join(destdir, specfile)
        shutil.copyfile(join(self.repo_basedir, 'etc', 'packaging', 'skel.spec'),
                        specfile_fp)

        # extract list of installed files from makefile
        makefile_fp = join(destdir, self.pkgname, 'Makefile')
        content = open(makefile_fp, 'rt').read()
        content = text.safefind('(?s)install:\s*.*', content)

        files = []
        lines = content.split('\n')
        for line in lines:
            if '${DESTDIR}' in line:
                parts = re.split('[ ]', line)
                path = parts[-1]
                path = re.sub('^' + re.escape('${DESTDIR}'), '', path)
                files.append(path)
        files.sort()

        # patch spec file
        context = {
            '(?m)^(Summary:\s*).*': '\g<1> {0}'.format(self.rpmmeta_summary),
            '(?m)^(Name:\s*).*': '\g<1> {0}'.format(self.name),
            '(?m)^(Version:\s*).*': '\g<1> {0}'.format(self.versiontag),
            '(?m)^(Release:\s*).*': '\g<1> {0}'.format(self.buildnum),
            '(?m)^(License:\s*).*': '\g<1> {0}'.format(self.license),
            '(?m)^(Group:\s*).*': '\g<1> {0}'.format(self.rpmmeta_group),
            '(?m)^(BuildArch:\s*).*': '\g<1> {0}'.format(self.rpmmeta_arch),
            '(?m)^(Source:\s*).*': '\g<1> {0}'.format(self.targz_name),
            '(?m)^(BuildRoot:\s*).*': '\g<1> {0}/%{{name}}-buildroot'.format(d),
            '(?m)^(Requires:\s*).*': '\g<1> {0}'.format(', '.join(self.rpmmeta_requires)),
            '(?m)^.*[<]desc[>].*': self.rpmmeta_desc,
            '(?m)^.*[<]files[>].*': '\n'.join(files),
        }
        text.patch_file(context, specfile_fp, dest=specfile_fp, literal=False)

        with warn_only():
            run_cmd('rpmbuild -ba {0} --define "_topdir {1}"'.format(
                specfile_fp, rpmbuild_dir))

    def pkg_rpm(self):
        with fs.mkdtemp() as d:
            self.do_pkg_rpm(destdir=d)

            rpmdir = join(d, 'rpmbuild', 'RPMS', self.rpmmeta_arch)
            files = os.listdir(rpmdir)
            files = fnmatch.filter(files, '*.rpm')
            shutil.copy(join(rpmdir, files[0]), self.product_dir)
