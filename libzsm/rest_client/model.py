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


from exc import InvalidAttribute


class Model(object):
    # NOTE: this needs to be a whitelist of names that can be assigned
    # without checking the schema (ie. which are not resource fields,
    # just misc attributes)
    _whitelisted_attributes = ['_store', '_resource']

    _resource = None

    def __init__(self, _atts=None, initial=None):
        '''NOTE: Important distinction between _atts and initial:
        _atts gets set directly on the model without serialization.
        initial gets set using the serializer.'''

        self._store = _atts or {}
        initial = initial or {}

        self.update_with(initial)

    @property
    def base_url(self):
        return self._resource.get_detail_uri(self)

    def get_parent_obj(self):
        if self._resource.parent:
            param_name = self._resource.parent.singular_name
            return getattr(self, param_name, None)

    def __eq__(self, other):
        if other:

            # if both have base_url, use that to compare
            if self.base_url and other.base_url:
                return self.base_url == other.base_url

            # and if both are not yet saved, use standard __eq__
            elif not self.base_url and not other.base_url:
                return super(Model, self).__eq__(other)

        return False

    def __cmp__(self, other):
        # sort by base_url
        return cmp(self.base_url, other.base_url)

    def __repr__(self):
        if self._store.get('id'):
            return "<{0}: {1}>".format(self.__class__.__name__, self.base_url)
        else:
            return "<{0}: (Not saved)>".format(self.__class__.__name__)

    ## Debug printing

    def pprint(self):
        ss = []
        for key in sorted(self._store):
            val = getattr(self, key)
            ss.append(u'{0:40}:  {1}'.format(key, val))
        return u'\n'.join(ss)

    def str(self):
        ss = []
        for key, val in sorted(self._store.items()):
            ss.append(u'{0:40}:  {1}'.format(key, val))
        return u'\n'.join(ss)

    ## Magic field getter/setter

    def __getattr__(self, key):
        try:
            value = self._store[key]
            schema_field = self._resource.schema.fields[key]
            value = schema_field.deserialize_value(value)
            return value
        except KeyError:
            raise InvalidAttribute(key)

    def __setattr__(self, key, value):
        if not key in self._whitelisted_attributes:
            try:
                schema_field = self._resource.schema.fields[key]
                value = schema_field.serialize_value(value)
                self._store[key] = value
            except KeyError:
                raise InvalidAttribute(key)

        else:
            return super(Model, self).__setattr__(key, value)

    def update_with(self, atts):
        assert type(atts) == dict

        for key, value in atts.items():
            setattr(self, key, value)

    ## Field access bypassing validation & serializer

    def bind_in_store(self, key, value):
        self._store[key] = value

    def get_bound(self):
        return self._store

    ## Instantiation

    @classmethod
    def get_class(cls, name):
        clsname = '{0}{1}'.format(name.title(), 'Model')
        model_class = type(clsname, (cls,), {})
        return model_class

    @classmethod
    def get_instance(cls, _atts=None, initial=None):
        _atts = _atts or {}
        initial = initial or {}

        return cls(_atts=_atts, initial=initial)
