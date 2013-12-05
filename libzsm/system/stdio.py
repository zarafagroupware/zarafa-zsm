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


def green(msg):
    return '\033[32m' + msg + '\033[0m'

def yellow(msg):
    return '\033[33m' + msg + '\033[0m'

def red(msg):
    return '\033[31m' + msg + '\033[0m'

def toggle_ansi(func):
    def new_func(*args, **kwargs):
        if not sys.stdout.isatty():
            return args[0]

        return func(*args, **kwargs)
    return new_func

green = toggle_ansi(green)
yellow = toggle_ansi(yellow)
red = toggle_ansi(red)


def puth(msg):
    write(green(msg + '\n'))

def putw(msg):
    write(yellow(msg + '\n'))

def pute(msg):
    write(red(msg + '\n'))

def write(msg):
    if isinstance(msg, unicode):
        msg = msg.encode('utf-8')
    sys.stdout.write(msg)
    sys.stdout.flush()

def writeln(msg):
    write(msg + '\n')

warn = putw
error = pute
ok = puth
info = write


def die(msg):
    writeln(msg)
    sys.exit(1)
