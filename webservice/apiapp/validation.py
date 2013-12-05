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
from tastypie.validation import Validation

from pumpkin_ext import extfields


class LdapResourceValidation(Validation):
    rx_base64_string = re.compile('^[A-Za-z0-9+/=]*$')

    def __init__(self, resource):
        self.resource = resource

        self.fieldmap = {
            fields.BinaryField: self.validate_binary,
            fields.BooleanField: self.validate_boolean,
            fields.DatetimeField: self.validate_datetime,
            fields.DatetimeListField: self.validate_noop,
            fields.DictField: self.validate_noop,
            fields.GeneralizedTimeField: self.validate_datetime,
            extfields.GeneralizedTimeField: self.validate_datetime,
            fields.IntegerField: self.validate_integer,
            fields.IntegerListField: self.validate_noop,
            fields.StringField: self.validate_unicode,
            fields.StringListField: self.validate_unicode_list,
            extfields.IntBooleanField: self.validate_boolean,
        }

    def validate_noop(self, resource_field, model_field, value):
        raise NotImplementedError

    def validate_binary(self, resource_field, model_field, value):
        if resource_field.null and value is None:
            pass

        elif not self.rx_base64_string.match(value):
            return u'Invalid base64 binary value'

    def validate_boolean(self, resource_field, model_field, value):
        if resource_field.null and value is None:
            pass

        elif not type(value) == bool:
            return u'Not a boolean'

    def validate_datetime(self, resource_field, model_field, value):
        pass  # TODO

    def validate_integer(self, resource_field, model_field, value):
        if resource_field.null and value is None:
            pass

        elif not type(value) == int:
            return u'Not an integer'

    def validate_unicode(self, resource_field, model_field, value):
        if resource_field.null and value is None:
            pass

        elif not type(value) == unicode:
            return u'Not a unicode string'

    def validate_unicode_list(self, resource_field, model_field, value):
        if resource_field.null and value is None:
            pass

        elif (not type(value) == list
              or not all([type(v) == unicode for v in value])):
            return u'Not a list of unicode strings'

    def is_valid(self, bundle, request=None):
        errors = {}

        # reject invalid fields
        for key in bundle.data:
            if not key in self.resource.base_fields:
                errors[key] = [u'Invalid field']
                continue

            resource_field = self.resource.fields[key]

            # handle non related fields
            if not getattr(resource_field, 'is_related', None):

                model_field = self.resource.get_model_field(key)

                # NOTE: skipping fields in resource but not in model (resource_uri)
                if model_field:
                    validator = self.fieldmap[model_field.__class__]

                    value = bundle.data[key]
                    err_msg = validator(resource_field, model_field, value)

                    if err_msg:
                        errors[key] = [err_msg]

        return errors
