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


import re
import uuid


class Reference(object):
    def __init__(self, pk=None):
        self.pk = pk or u'{0}'.format(uuid.uuid4().hex)

    def __str__(self):
        return self.pk


class FixtureMeta(type):
    def __new__(cls, name, bases, kwargs):
        cls_obj = super(FixtureMeta, cls).__new__(cls, name, bases, kwargs)

        # figure out all the bases
        mro_chain = cls_obj.mro()
        mro_chain.reverse()

        dct = {}

        # grab fields from all bases
        for c in mro_chain[:-1]:
            if getattr(c, '__metaclass__', None) == cls:
                dct.update(c._fields)

        # overlay fields from the new class
        for att, value in kwargs.items():
            if re.search(r'^[A-Za-z]', att):
                dct[att] = value

        cls_obj._fields = dct

        return cls_obj

    def _hash_value(cls, value):
        total = 0
        if isinstance(value, Reference):
            pass
        elif type(value) == list:
            total = sum([cls._hash_value(e) for e in value])
        else:
            total = hash(value)
        return total

    def __hash__(cls):
        '''Hash based on field values.'''
        total = 0
        for value in cls._fields.values():
            total += cls._hash_value(value)
        return total


class FixtureBase(object):
    __metaclass__ = FixtureMeta

    _fields = {}


def mutate(cls):
    new_dct = {}

    for fname, value in cls._fields.items():
        if isinstance(value, basestring):
            import uuid
            suffix = uuid.uuid4().hex[4:10]
            value = u'{0}{1}'.format(value, suffix)

        elif type(value) == bool:
            value = not value

        #elif type(value) == int:
        #    value += 1

        new_dct[fname] = value

    new_cls = cls.__metaclass__('{0}Mutant'.format(cls.__name__), cls.__bases__, new_dct)
    return new_cls
