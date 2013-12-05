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


from collections import Iterable
import logging

from pumpkin import fields
from pumpkin.filters import eq
import pumpkin.models

from libzsm.datehelper import utcnow

from acl import Ace
from acl import Acl
from acl import Privileges
from ldapdirectory import get_directory
from loaders.models import get_model

logger = logging.getLogger(__name__)


def generate_uuid():
    import uuid
    return u'{0}'.format(uuid.uuid4().hex)


class ModelBase(pumpkin.models.Model):
    def __init__(self, directory=None, dn=None, attrs=None, initial=None):
        '''NOTE: directory, dn and attrs are all arguments to the base class
        __init__ and used internally by pumpkin (ie. cannot be changed.)

        The attrs parameter is handled as "raw" ldap values, where each value
        must be a list of str.

        By contrast, the initial parameter works just like setting attributes
        on instances of the object, so it takes type correct values
        (ints, unicode etc.)'''

        attrs = attrs or {}
        initial = initial or {}

        if not directory:
            directory = get_directory()

        super(ModelBase, self).__init__(directory, dn=dn, attrs=attrs)

        for key, val in initial.items():
            setattr(self, key, val)

    def str(self):
        fmt = u'{0:32} {1}'
        ss = [fmt.format(u'dn', self.dn)]
        for key in sorted(self.ldap_attributes()):
            ss.append(fmt.format(key, getattr(self, key, None)))
        return u'\n'.join(ss)

    def _set_parent(self, parent):
        self.set_parent(parent.dn)
    parent = property(fset=_set_parent)

    def get_mandatory_fields(self):
        return [self._rdn_] + getattr(self, '_mandatory_fields_', [])

    # ORM services

    @classmethod
    def get_object(cls, fieldname, value):
        directory = get_directory()
        object_list = directory.search(
            cls,
            search_filter=eq(getattr(cls, fieldname), value)
        )
        if object_list:
            return object_list[0]

    def save(self, *args, **kwargs):
        # generate a zarafaId if not set
        if ('zarafaId' in self._get_fields()
            and not self.zarafaId):
            self.zarafaId = generate_uuid()

        # special case certain types of fields
        for fname, field_object in self._fields.items():
            value = getattr(self, fname)

            # unset fields that are an empty list, python-ldap blows up
            # value can also be a MockManager
            if isinstance(value, Iterable) and len(value) == 0:
                delattr(self, fname)

            # encode binary fields
            elif isinstance(field_object, fields.BinaryField) and value:
                value = value.encode('utf8')
                setattr(self, fname, value)

        logger.debug(u'Saving model:\n{0}'.format(self.str()))
        return super(ModelBase, self).save(*args, **kwargs)

    def save_or_update(self, *args, **kwargs):
        '''If the object exists, update its attributes from the new
        object. Otherwise create it.'''

        # Search for existing node. If found, update it.
        if self.dn:
            rdn_key = getattr(self.__class__, '_rdn_')
            rdn_val = getattr(self, self._rdn_)

            object_list = self.directory.search(
                self.__class__,
                basedn=self._parent,
                recursive=False,
                search_filter=eq(rdn_key, rdn_val),
            )

            if object_list:
                self_old = object_list[0]
                for fname, field_object in self._fields.items():
                    if fname in ['object_class']:
                        continue

                    val_new = getattr(self, fname, None)
                    if val_new:
                        setattr(self_old, fname, val_new)

                return self_old.save()

        return self.save(*args, **kwargs)

    # Permissions

    def has_acl_perm(self, perm, target):
        acl = Acl.parse(target.zarafaACL)

        is_granted = False
        if acl.has_perm(perm, self):
            is_granted = True

        if not is_granted:
            user_groups = self.memberOf.all()
            for ace in acl.aces:
                if ace.group_id:
                    model = get_model('models_ldap.Group')
                    group = model.get_object('zarafaId', ace.group_id)
                    if group.zarafaId in [g.zarafaId for g in user_groups]:
                        if acl.has_perm(perm, group):
                            is_granted = True

        return is_granted

    def has_privilege_perm(self, perm):
        privs = Privileges.parse(self.zarafaApiPrivileges)

        is_granted = False
        if privs.has_perm(perm):
            is_granted = True

        if not is_granted:
            for group in self.memberOf:
                privs = Privileges.parse(group.zarafaApiPrivileges)
                if privs.has_perm(perm):
                    is_granted = True

        return is_granted

    def has_perm(self, perm, target=None):
        if target:
            return self.has_acl_perm(perm, target)
        return self.has_privilege_perm(perm)

    def set_acl(self, perm_names, user=None, group=None):
        assert user or group

        kwargs = {}
        if user:
            kwargs['user_id'] = user.zarafaId
        elif group:
            kwargs['group_id'] = group.zarafaId

        ace = Ace(perm_names, **kwargs)
        acl = Acl([ace])
        self.zarafaACL = acl.format()

    def set_privs(self, perm_names):
        privs = Privileges(perm_names)
        self.zarafaApiPrivileges = privs.format()

    # Other actions

    def soft_delete(self):
        # do not update timestamp
        if not self.zarafaSoftDeletedDate:
            self.zarafaSoftDeletedDate = utcnow()

        self.zarafaAccount = False
        self.save()

    def soft_undelete(self):
        self.zarafaSoftDeletedDate = None
        self.zarafaAccount = True
        self.save()
