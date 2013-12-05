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


import fnmatch
import grp
import os
import pwd
import re
import shutil
import tempfile

from fabric.api import quiet

from proc import run_cmd


def chown(path, user, group):
    uid = pwd.getpwnam(user)[2] if user else -1
    guid = grp.getgrnam(group)[2] if group else -1

    os.chown(path, uid, guid)


def gluejoin(a, *args):
    args = list(args)

    for i, arg in enumerate(args):
        if arg.startswith('/'):
            arg = arg[1:]
        args[i] = arg

    args = [a] + args
    return os.path.join(*args)


def listdir_recursive(cwd):
    '''Returns files only.'''
    files = []

    for r, _, fs in os.walk(cwd):
        r = r + '/' if not r.endswith('/') else r
        relroot = re.sub(re.escape(cwd + '/'), '', r)
        for f in fs:
            path = os.path.join(relroot, f)
            files.append(path)

    return files


def makedirs(path, user=None, group=None):
    os.makedirs(path)
    if user or group:
        chown(path, user, group)


def merge_fileset(files, srcdir, destdir):
    for f in files:
        d = os.path.dirname(f)
        dest = os.path.join(destdir, d)
        if not os.path.exists(dest):
            os.makedirs(dest)

        shutil.copy2(
            os.path.join(srcdir, f),
            os.path.join(destdir, f)
        )


class mkstemp(object):
    def __enter__(self):
        self.fd, self.fp = tempfile.mkstemp()
        return self.fp

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.unlink(self.fp)
        os.close(self.fd)


class mkdtemp(object):
    def __enter__(self):
        self.directory = tempfile.mkdtemp()
        return self.directory

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self.directory)


def rm(cwd, pat):
    files = os.listdir(cwd)
    files = fnmatch.filter(files, pat)
    for f in files:
        fp = os.path.join(cwd, f)
        os.unlink(fp)


def sh_cat(path, **kwargs):
    with quiet():
        return run_cmd('cat {0}'.format(path), capture=True, **kwargs)


def sh_chmod(path, mask, **kwargs):
    with quiet():
        return run_cmd('chmod {0} {1}'.format(mask, path), capture=True, **kwargs)


def sh_chown(path, user=None, group=None, recursive=False, **kwargs):
    if user:
        mask = '{0}'.format(user)
        if group:
            mask = '{0}:{1}'.format(mask, group)

    with quiet():
        extra_args = ''
        if recursive:
            extra_args = ' -R'
        return run_cmd('chown {0} {1} {2}'.format(extra_args, mask, path), capture=True, **kwargs)


def sh_copyfile(src, dest, **kwargs):
    with quiet():
        return run_cmd('cp {0} {1}'.format(src, dest), capture=True, **kwargs)


def sh_copytree(src, dest, **kwargs):
    with quiet():
        return run_cmd('cp -r {0} {1}'.format(src, dest), capture=True, **kwargs)


def sh_dir_exists(path, **kwargs):
    with quiet():
        return run_cmd('test -d {0}'.format(path), **kwargs).succeeded


def sh_exists(path, **kwargs):
    with quiet():
        return run_cmd('test -e {0}'.format(path), **kwargs).succeeded


def sh_file_exists(path, **kwargs):
    with quiet():
        return run_cmd('test -f {0}'.format(path), **kwargs).succeeded


def sh_ln(src, dest, symbolic=True, **kwargs):
    with quiet():
        sym = ' -s' if symbolic else ''
        return run_cmd('ln{0} {1} {2}'.format(sym, src, dest), **kwargs).succeeded


def sh_listdir(path, **kwargs):
    with quiet():
        content = run_cmd('find {0} -maxdepth 1'.format(path), **kwargs)

    items = content.split('\n')
    items = [item.strip() for item in items]
    esc = lambda path: re.escape(path + '/' if not path.endswith('/') else path)
    items = [re.sub('^' + esc(path), '', item) for item in items]
    items = [item for item in items if item and not item == path]
    return items


def sh_makedirs(path, user=None, group=None, **kwargs):
    with quiet():
        run_cmd('mkdir -p {0}'.format(path), **kwargs)

        mask = '{0}:{1}'.format(user or '', group or '')
        run_cmd('chown {0} {1}'.format(mask, path), **kwargs)


def sh_mktemp(base_path, directory=True, **kwargs):
    with quiet():
        args = ['--tmpdir={0}'.format(base_path)]
        if directory:
            args.append('-d')

        args = ' '.join(args)
        return run_cmd('mktemp {0}'.format(args), **kwargs)


def sh_rm(path, **kwargs):
    with quiet():
        return run_cmd('rm -f {0}'.format(path), **kwargs)


def sh_rmtree(path, **kwargs):
    with quiet():
        return run_cmd('find {0} -delete'.format(path), **kwargs)


def sh_which(path, **kwargs):
    with quiet():
        return run_cmd('which {0}'.format(path), **kwargs)
