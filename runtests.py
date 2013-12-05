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



from optparse import OptionParser

from libzsm.system.proc import invoke

RUNSERVER_PORT = 8000

COVERAGE_DIRS = [
    'libzsm',
    'tests',
]


class TestRunner(object):
    def list(self):
        args = ['nosetests', '--collect-only', '-v']
        invoke(args)

    def run(self, with_coverage=False, with_regex=None,
            verbosity=0,
            pdb_error=False, pdb_failure=False):
        args = ['nosetests', '--rednose']

        if with_coverage:
            args.extend(['--with-cov', '--cov-report', 'term-missing'])
            for d in COVERAGE_DIRS:
                args.extend(['--cov', d])

        if with_regex:
            args.extend(['-t', with_regex])

        if verbosity > 0:
            arg = 'v' * verbosity
            args.append('-{0}'.format(arg))

        if pdb_error or pdb_failure:
            pdb = 'pdb'
            try:
                import ipdb  # NOQA
                pdb = 'ipdb'
            except ImportError:
                pass

            if pdb_error:
                args.append('--{0}'.format(pdb))
            if pdb_failure:
                args.append('--{0}-failures'.format(pdb))

        invoke(args)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--cov', dest='with_coverage', action='store_true',
                      help='Run tests under coverage.')
    parser.add_option('-l', '--list', dest='do_list', action='store_true',
                      help='Only list the tests.')
    parser.add_option('-t', dest='regex', action='store',
                      help='Only run tests matching regex.')
    parser.add_option('-v', dest='verbosity', action='count',
                      help='Verbosity level eg. -vv.')
    parser.add_option('--pdb', dest='pdb_error', action='store_true',
                      help='Drop into debugger on errors.')
    parser.add_option('--pdb-failures', dest='pdb_failure', action='store_true',
                      help='Drop into debugger on failures.')
    options, args = parser.parse_args()

    runner = TestRunner()

    if options.do_list:
        runner.list()
    else:
        runner.run(
            with_coverage=options.with_coverage,
            with_regex=options.regex,
            verbosity=options.verbosity,
            pdb_error=options.pdb_error,
            pdb_failure=options.pdb_failure,
        )
