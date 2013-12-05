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


from pumpkin import fields
from pumpkin.exceptions import ObjectNotFound
from pumpkin.filters import eq

from libzsm.pumpkin_ext.extfields import GeneralizedTimeField  # NOQA

from dn import Dn
from apiapp.loaders.models import get_model
from apiapp.tastypie_ext.mocks import MockManager


class LdapRelatedVirtualField(object):
    '''NOTE: We do not inherit from pumpkin.fields.Field because that will cause
    pumpkin to try to write the field to LDAP, whereas it's actually a virtual
    field that has a side effect only.'''
    def __init__(self, **kwargs):
        self.intermediate = kwargs.pop('intermediate')
        self.to_model = kwargs.pop('to_model')
        self.up_tree = kwargs.pop('up_tree', False)
        self.down_tree = kwargs.pop('down_tree', False)


class LdapToOneVirtualField(LdapRelatedVirtualField):
    def __get__(self, instance, instance_type=None):
        pk = Dn(instance.dn).parent.parent.rdn_value  # handle up/down tree
        to_model = get_model(self.to_model)
        models = instance.directory.search(to_model, search_filter=eq(to_model._rdn_, pk))
        return models[0]

    def __set__(self, instance, value):
        if not value is None:
            # validate value of type self.to_model ?
            path = Dn(value.dn).child(self.intermediate).dn_path  # handle up/down tree
            instance.set_parent(path)


class LdapToManyVirtualField(LdapRelatedVirtualField):
    def __get__(self, instance, instance_type=None):
        model_dn = Dn(instance.dn).child(self.intermediate).dn_path
        to_model = get_model(self.to_model)
        models = []
        try:
            models = instance.directory.search(to_model, basedn=model_dn)
        except ObjectNotFound:
            pass
        return MockManager(models)


class LdapToOneField(fields.StringField):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.to_model = kwargs.pop('to_model')
        # store only rdn value in the ldap attribute, not the whole dn
        self.rdn_is_fk = kwargs.pop('rdn_is_fk', None)

        super(LdapToOneField, self).__init__(name, *args, **kwargs)

    def fget(self, instance):
        dns = instance._get_attr(self.name)
        if dns:
            if self.rdn_is_fk:
                pk = dns[0]
            else:
                pk = Dn(dns[0]).rdn_value

            to_model = get_model(self.to_model)
            models = instance.directory.search(to_model, search_filter=eq(to_model._rdn_, pk))
            return models[0]

    def fset(self, instance, value):
        if not value is None:
            arg = value.dn
            if self.rdn_is_fk:
                arg = Dn(value.dn).rdn_value

            return super(LdapToOneField, self).fset(instance, arg)
        else:
            self.fdel(instance)


class LdapToManyField(fields.StringListField):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.to_model = kwargs.pop('to_model')
        # store only rdn value in the ldap attribute, not the whole dn
        self.rdn_is_fk = kwargs.pop('rdn_is_fk', None)
        self.rdn_field = kwargs.pop('rdn_field', None)
        self.parent_dn = kwargs.pop('parent_dn', None)

        super(LdapToManyField, self).__init__(name, *args, **kwargs)

    def fget(self, instance):
        models = []
        to_model = get_model(self.to_model)
        try:
            dns = instance._get_attr(self.name)
            if dns:
                if self.parent_dn:
                    f = lambda dn: u'{0}={1}'.format(self.rdn_field, dn)
                    dns = [Dn(self.parent_dn).child(f(dn)).dn_path for dn in dns]

                models = [instance.directory.search(to_model, basedn=dn)[0]
                          for dn in dns]
        except ObjectNotFound:
            pass
        return MockManager(models)

    def fset(self, instance, values):
        if values is not None:
            args = [i.dn for i in values]
            if self.rdn_is_fk:
                args = [Dn(i.dn).rdn_value for i in values]

            return super(LdapToManyField, self).fset(instance, args)


class IntBooleanField(fields.IntegerField):
    def encode2str(self, values, instance=None):
        return super(IntBooleanField, self).encode2str(int(values), instance=instance)

    def decode2local(self, values, instance=None):
        values = super(IntBooleanField, self).decode2local(values, instance=instance)
        return bool(values)
