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

from pumpkin import fields
from pumpkin.base import _model
import pumpkin.base

from libzsm.pumpkin_ext import extfields


class Field(object):
    def __init__(self, name, field_class):
        self.name = name
        self.field_class = field_class

    def get_instance(self, remote_name):
        # NOTE: make sure it's not unicode, python-ldap crashes
        remote_name = str(remote_name)
        return self.field_class(remote_name)


class Model(pumpkin.base.Model):
    def __init__(self, directory, dn=None, attrs={}):
        '''Overload to omit failing _validate_object_class check.'''

        self._storage = {}
        for (attr, value) in attrs.items():
            self._store_attr(attr, value)
        if attrs != {}:
            for instance in self._get_fields().values():
                if not self._isstored(instance.attr):
                    if not instance.lazy:
                        self._store_attr(instance.attr, None)

        if dn:
            if isinstance(dn, unicode):
                self._dn = dn
            else:
                self._dn = unicode(dn, 'utf-8')
        else:
            self._dn = None

        # used when changing object dn
        self._olddn = None

        self.directory = directory

        self._validate_rdn_fields()
        self._validate_schema()

        if dn is None:
            self._empty = True
            self._parent = self.directory.get_basedn()
        else:
            self._empty = False
            self._parent = None

            self.update(missing_only=True)
            # raises weird KeyError for self.object_class
            #self._validate_object_class()


class ModelBuilder(object):
    def __init__(self, remote_conf):
        self.remote_conf = remote_conf

        self.base_fields = [
            Field('remoteId', fields.StringField),
            Field('remoteChangedDate', extfields.GeneralizedTimeField),
        ]

        self.tenant_object_classes = self.remote_conf.TENANT_OBJECT_CLASSES
        self.tenant_fields = [
            Field('name', fields.StringField),
        ]

        self.user_object_classes = self.remote_conf.USER_OBJECT_CLASSES
        self.user_fields = [
            Field('username', fields.StringField),
            Field('surname', fields.StringField),
            Field('name', fields.StringField),
            Field('mail', fields.StringField),
            Field('initials', fields.StringField),
            Field('description', fields.StringField),
        ]

        self.group_object_classes = self.remote_conf.GROUP_OBJECT_CLASSES
        self.group_fields = [
            Field('name', fields.StringField),
            Field('members', fields.StringListField),
        ]

        self.contact_object_classes = self.remote_conf.CONTACT_OBJECT_CLASSES
        self.contact_fields = [
            Field('name', fields.StringField),
            Field('surname', fields.StringField),
            Field('mail', fields.StringField),
        ]

    def get_field_dict(self, blueprint, section):
        dct = {}

        def trans(match):
            return '%s_%s' % (match.group(1), match.group(2).lower())

        for field in blueprint:
            name = re.sub('([a-z])([A-Z])', trans, field.name)
            config_name = '%s_%s' % (section, name)
            config_name = config_name.upper()

            remote_name = getattr(self.remote_conf, config_name, None)
            if remote_name:
                instance = field.get_instance(remote_name)
                dct[field.name] = instance

        return dct

    def get_model(self, name, field_spec, object_classes):
        dct = self.get_field_dict(self.base_fields, 'common')
        RemoteModel = _model('RemoteModel', (Model,), dct)

        dct = self.get_field_dict(field_spec, name.lower())
        dct.update({
            '_object_class_': object_classes,
        })

        cls = _model(name, (RemoteModel,), dct)

        return cls

    def get_tenant(self):
        return self.get_model(
            'Tenant',
            self.tenant_fields,
            self.tenant_object_classes,
        )

    def get_user(self):
        return self.get_model(
            'User',
            self.user_fields,
            self.user_object_classes,
        )

    def get_group(self):
        return self.get_model(
            'Group',
            self.group_fields,
            self.group_object_classes,
        )

    def get_contact(self):
        return self.get_model(
            'Contact',
            self.contact_fields,
            self.contact_object_classes,
        )
