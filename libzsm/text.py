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


import os
import random
import re


def get_random_unichar():
    '''This needs to be a valid ldap DN char, so try to stay conservative
    to avoid hitting non-printable and formatting characters.'''
    # ref: http://jrgraphix.net/research/unicode_blocks.php
    ranges = [
        (0x0100, 0x017f),  # Latin Extended-A
        (0x1e00, 0x1eff),  # Latin Extended Additional
        (0x3041, 0x3096),  # Hiragana
        (0x7930, 0x7d2f),  # CJK Unified Ideographs
    ]
    range = random.choice(ranges)
    i = random.randint(*range)
    return unichr(i)

def get_random_unistr(length):
    s = [get_random_unichar() for i in range(length)]
    return ''.join(s)


def make_plural(s):
    if not s.endswith('s'):
        return '{0}s'.format(s)
    return s

def make_singular(s):
    return re.sub('s$', '', s)


def patch(context, content, literal=True):
    for needle, repl in context.items():
        if literal:
            needle = re.escape(needle)

        new_content = re.sub(needle, repl, content)

        # check if rewrite actually happened
        if content == new_content:
            if not re.search(needle, content):
                raise Exception('Did not find needle: {0}'. format(needle))

        content = new_content

    return content


def patch_file(context, path, dest=None, **kwargs):
    assert os.path.isfile(path)
    assert dest is not None

    content = open(path, 'rt').read()
    content = patch(context, content, **kwargs)
    open(dest, 'wt').write(content)


def patch_config_file(context, *args, **kwargs):
    new_context = {}
    for key, val in context.items():
        if val:
            val = '{0} = {1}'.format(key, val)
            key = '(?m)^' + re.escape(key) + '\s*[=].*$'
            new_context[key] = val

    kwargs.update({
        'literal': False,
    })
    return patch_file(new_context, *args, **kwargs)


def safefind(needle, text):
    try:
        return re.findall(needle, text)[0]
    except IndexError:
        pass
