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


from django.core.urlresolvers import reverse

import tastypie.resources

from pumpkin import fields

from libzsm.fixtures import registry
from libzsm import text


_fieldmap = {
    fields.BinaryField: u'base64',
    fields.BooleanField: u'bool',
    fields.DatetimeField: u'datetime',
    fields.DatetimeListField: u'list of datetime',
    fields.DictField: u'{}',
    fields.GeneralizedTimeField: u'list of generalizeddatetime',
    fields.IntegerField: u'integer',
    fields.IntegerListField: u'list of int',
    fields.StringField: u'string',
    fields.StringListField: u'list of string',
}

def get_ldap_field_signature(field):
    global _fieldmap
    return _fieldmap.get(field)


def get_resource_detail_uri(resource, id):
    assert isinstance(id, basestring)
    assert isinstance(resource, tastypie.resources.Resource)

    view_name = resource.get_view_name_detail()
    kwargs = resource.get_detail_view_kwargs()

    # fetch all the ids
    fix = registry.get_single_fixture_by_id(id)
    ids = {
        resource._meta.resource_name: fix.id.pk,
    }

    cur = resource
    i = id
    while cur.parent:
        field_name = text.make_singular(cur.parent._meta.resource_name)
        i = getattr(getattr(fix, field_name, None), 'pk', None)
        fix = registry.get_single_fixture_by_id(i)
        i = fix.id.pk
        ids[cur.parent._meta.resource_name] = i

        cur = cur.parent

    for key, value in kwargs.items():
        parts = key.split('_')
        if len(parts) == 2:
            [name, pk] = parts
            if pk == 'pk':
                kwargs[key] = ids[name]

    uri = reverse(view_name, kwargs=kwargs)
    return uri
