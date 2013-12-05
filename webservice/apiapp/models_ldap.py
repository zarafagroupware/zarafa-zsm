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

from ldapdirectory import get_directory
from ldapmodelbase import ModelBase
from mapibackend.storebackend import StoreBackend
from pumpkin_ext import extfields
from pumpkin_ext.dn import Dn

from conf.settings import config


PARENT_DN_SERVER = 'ou=servers,dc=zarafa'

class RootNode(ModelBase):
    _object_class_ = ['dcObject', 'organization']
    _rdn_ = 'dc'
    dc = fields.StringField('dc')
    o = fields.StringField('o')

    @classmethod
    def load_root(cls):
        directory = get_directory()
        entries = directory.search(cls, basedn=config.LDAP_BASEDN)
        return entries[0]


class Unit(ModelBase):
    _object_class_ = ['organizationalUnit']
    _rdn_ = 'ou'
    ou = fields.StringField('ou')


class Server(ModelBase):
    _object_class_ = ['zarafa-server', 'ipHost', 'device', 'top']
    _rdn_ = 'cn'
    _parent_dn_ = PARENT_DN_SERVER
    zarafaId = fields.StringField('zarafaId')
    cn = fields.StringField('cn')
    zarafaAccount = extfields.IntBooleanField('zarafaAccount')
    zarafaHidden = extfields.IntBooleanField('zarafaHidden')
    ipHostNumber = fields.StringField('ipHostNumber')
    zarafaHttpPort = fields.IntegerField('zarafaHttpPort')
    zarafaSslPort = fields.IntegerField('zarafaSslPort')
    zarafaFilePath = fields.StringField('zarafaFilePath')
    zarafaContainsPublic = extfields.IntBooleanField('zarafaContainsPublic')
    zarafaProxyURL = fields.StringField('zarafaProxyURL')

    def save(self, *args, **kwargs):
        self.set_parent(self._parent_dn_)
        return super(Server, self).save(*args, **kwargs)


class Tenant(ModelBase):
    _object_class_ = ['zarafa-company', 'zarafa-aclobj']
    _rdn_ = 'o'
    _parent_dn_ = 'ou=tenants,dc=zarafa'
    zarafaId = fields.StringField('zarafaId')
    pk = fields.StringField('zarafaId')
    o = fields.StringField('o')
    zarafaAccount = extfields.IntBooleanField('zarafaAccount')
    zarafaHidden = extfields.IntBooleanField('zarafaHidden')
    zarafaMailDomains = fields.StringListField('zarafaMailDomains')
    zarafaViewPrivilege = extfields.LdapToManyField(
        'zarafaViewPrivilege', to_model='models_ldap.Tenant')
    zarafaAdminPrivilege = extfields.LdapToManyField(
        'zarafaAdminPrivilege', to_model='models_ldap.User')
    zarafaSystemAdmin = extfields.LdapToOneField(
        'zarafaSystemAdmin', to_model='models_ldap.User')
    zarafaACL = fields.StringListField('zarafaACL')
    zarafaQuotaOverride = extfields.IntBooleanField('zarafaQuotaOverride')
    zarafaQuotaWarn = fields.IntegerField('zarafaQuotaWarn')
    zarafaUserDefaultQuotaOverride = extfields.IntBooleanField('zarafaUserDefaultQuotaOverride')
    zarafaUserDefaultQuotaWarn = fields.IntegerField('zarafaUserDefaultQuotaWarn')
    zarafaUserDefaultQuotaSoft = fields.IntegerField('zarafaUserDefaultQuotaSoft')
    zarafaUserDefaultQuotaHard = fields.IntegerField('zarafaUserDefaultQuotaHard')
    zarafaQuotaUserWarningRecipients = extfields.LdapToManyField(
        'zarafaQuotaUserWarningRecipients', to_model='models_ldap.User')
    zarafaQuotaCompanyWarningRecipients = extfields.LdapToManyField(
        'zarafaQuotaCompanyWarningRecipients', to_model='models_ldap.User')
    zarafaCompanyServer = extfields.LdapToOneField(
        'zarafaCompanyServer', rdn_is_fk=True, to_model='models_ldap.Server')
    zarafaRemoteChangedDate = extfields.GeneralizedTimeField('zarafaRemoteChangedDate')
    zarafaRemoteId = fields.StringField('zarafaRemoteId')
    users = extfields.LdapToManyVirtualField(
        to_model='models_ldap.User',
        down_tree=True, intermediate='ou=users')
    groups = extfields.LdapToManyVirtualField(
        to_model='models_ldap.Group',
        down_tree=True, intermediate='ou=groups')
    contacts = extfields.LdapToManyVirtualField(
        to_model='models_ldap.Contact',
        down_tree=True, intermediate='ou=contacts')

    @classmethod
    def get_dn(self, o):
        rdn = u'{0}={1}'.format(self._rdn_, o)
        return Dn(self._parent_dn_).child(rdn).dn_path

    def save(self, *args, **kwargs):
        self.set_parent(self._parent_dn_)

        creating = self.isnew()

        res = super(Tenant, self).save(*args, **kwargs)

        # create expected sub-units
        if creating:
            u = Unit(initial=dict(ou=u'users'))
            u.parent = self
            u.save()

            u = Unit(initial=dict(ou=u'groups'))
            u.parent = self
            u.save()

            u = Unit(initial=dict(ou=u'contacts'))
            u.parent = self
            u.save()

        return res

    def delete(self, recursive=False):
        '''Deleting a tenant isn't possible without recursive=True
        because it always contains sub nodes.'''
        return super(self.__class__, self).delete(recursive=True)


class User(ModelBase):
    _object_class_ = ['zarafa-user']
    _rdn_ = 'uid'
    _mandatory_fields_ = ['cn', 'sn']
    zarafaId = fields.StringField('zarafaId')
    pk = fields.StringField('zarafaId')
    uid = fields.StringField('uid')
    userPassword = fields.StringField('userPassword')
    mail = fields.StringField('mail')
    cn = fields.StringField('cn')
    sn = fields.StringField('sn')
    zarafaAliases = fields.StringListField('zarafaAliases')
    zarafaForwardAddress = fields.StringField('zarafaForwardAddress')
    zarafaSendAsPrivilege = extfields.LdapToManyField(
        'zarafaSendAsPrivilege', to_model='models_ldap.User')
    zarafaUserServer = extfields.LdapToOneField(
        'zarafaUserServer', rdn_is_fk=True, to_model='models_ldap.Server')
    zarafaAccount = extfields.IntBooleanField('zarafaAccount')
    zarafaSoftDeletedDate = extfields.GeneralizedTimeField('zarafaSoftDeletedDate')
    zarafaAdmin = fields.IntegerField('zarafaAdmin')
    zarafaApiPrivileges = fields.StringListField('zarafaApiPrivileges')
    zarafaEnabledFeatures = fields.StringListField('zarafaEnabledFeatures')
    zarafaDisabledFeatures = fields.StringListField('zarafaDisabledFeatures')
    zarafaQuotaOverride = extfields.IntBooleanField('zarafaQuotaOverride')
    zarafaQuotaWarn = fields.IntegerField('zarafaQuotaWarn')
    zarafaQuotaSoft = fields.IntegerField('zarafaQuotaSoft')
    zarafaQuotaHard = fields.IntegerField('zarafaQuotaHard')
    zarafaSharedStoreOnly = extfields.IntBooleanField('zarafaSharedStoreOnly')
    zarafaUserArchiveServers = extfields.LdapToManyField(
        'zarafaUserArchiveServers', to_model='models_ldap.Server',
        rdn_is_fk=True, rdn_field=Server._rdn_, parent_dn=PARENT_DN_SERVER)
    telephoneNumber = fields.StringField('telephoneNumber')
    mobile = fields.StringField('mobile')
    homePhone = fields.StringField('homePhone')
    facsimileTelephoneNumber = fields.StringField('facsimileTelephoneNumber')
    pager = fields.StringField('pager')
    jpegPhoto = fields.BinaryField('jpegPhoto')
    description = fields.StringField('description')
    departmentNumber = fields.StringField('departmentNumber')
    physicalDeliveryOfficeName = fields.StringField('physicalDeliveryOfficeName')
    l = fields.StringField('l')  # locality
    title = fields.StringField('title')
    initials = fields.StringField('initials')
    preferredLanguage = fields.StringField('preferredLanguage')
    employeeNumber = fields.StringField('employeeNumber')
    postalAddress = fields.StringField('postalAddress')
    st = fields.StringField('st')  # state
    street = fields.StringField('street')
    postalCode = fields.StringField('postalCode')
    postOfficeBox = fields.StringField('postOfficeBox')
    zarafaRemoteChangedDate = extfields.GeneralizedTimeField('zarafaRemoteChangedDate')
    zarafaRemoteId = fields.StringField('zarafaRemoteId')
    tenant = extfields.LdapToOneVirtualField(
        to_model='models_ldap.Tenant',
        up_tree=True, intermediate='ou=users')
    memberOf = extfields.LdapToManyField(
        'memberOf', readonly=True, to_model='models_ldap.Group')

    ## Relational fields

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)

        self._store = None

    def get_store(self):
        if not self._store:
            storebackend = StoreBackend.get()
            self._store = storebackend.get_user_store(self.userid)
        return self._store

    @property
    def userid(self):
        return u'{0}@{1}'.format(self.uid, self.tenant.o)

    @classmethod
    def get_by_userid(self, userid):
        uid, o = None, None
        try:
            [uid, o] = userid.rsplit('@', 1)
        except ValueError:
            pass

        if uid and o:
            users = []
            try:
                users = get_directory().search(
                    User,
                    basedn=Tenant.get_dn(o),
                    search_filter=eq(User.uid, uid),
                )
            except ObjectNotFound:
                pass

            if users:
                user = users[0]
                return user


class Group(ModelBase):
    _object_class_ = ['zarafa-group']
    _rdn_ = 'cn'
    zarafaId = fields.StringField('zarafaId')
    pk = fields.StringField('zarafaId')
    cn = fields.StringField('cn')
    member = extfields.LdapToManyField(
        'member', to_model='models_ldap.User')
    mail = fields.StringField('mail')
    zarafaAliases = fields.StringListField('zarafaAliases')
    zarafaSendAsPrivilege = extfields.LdapToManyField(
        'zarafaSendAsPrivilege', to_model='models_ldap.User')
    zarafaAccount = extfields.IntBooleanField('zarafaAccount')
    zarafaApiPrivileges = fields.StringListField('zarafaApiPrivileges')
    zarafaHidden = extfields.IntBooleanField('zarafaHidden')
    zarafaSecurityGroup = extfields.IntBooleanField('zarafaSecurityGroup')
    zarafaRemoteChangedDate = extfields.GeneralizedTimeField('zarafaRemoteChangedDate')
    zarafaRemoteId = fields.StringField('zarafaRemoteId')
    tenant = extfields.LdapToOneVirtualField(
        to_model='models_ldap.Tenant',
        up_tree=True, intermediate='ou=groups')


class Contact(ModelBase):
    _object_class_ = ['zarafa-contact']
    _rdn_ = 'zarafaId'
    zarafaId = fields.StringField('zarafaId')
    pk = fields.StringField('zarafaId')
    mail = fields.StringField('mail')
    cn = fields.StringField('cn')
    sn = fields.StringField('sn')
    zarafaAliases = fields.StringListField('zarafaAliases')
    zarafaSendAsPrivilege = extfields.LdapToManyField(
        'zarafaSendAsPrivilege', to_model='models_ldap.User')
    zarafaAccount = extfields.IntBooleanField('zarafaAccount')
    zarafaHidden = extfields.IntBooleanField('zarafaHidden')
    telephoneNumber = fields.StringField('telephoneNumber')
    mobile = fields.StringField('mobile')
    homePhone = fields.StringField('homePhone')
    facsimileTelephoneNumber = fields.StringField('facsimileTelephoneNumber')
    pager = fields.StringField('pager')
    jpegPhoto = fields.BinaryField('jpegPhoto')
    description = fields.StringField('description')
    departmentNumber = fields.StringField('departmentNumber')
    physicalDeliveryOfficeName = fields.StringField('physicalDeliveryOfficeName')
    l = fields.StringField('l')  # locality
    title = fields.StringField('title')
    initials = fields.StringField('initials')
    preferredLanguage = fields.StringField('preferredLanguage')
    employeeNumber = fields.StringField('employeeNumber')
    postalAddress = fields.StringField('postalAddress')
    st = fields.StringField('st')  # state
    street = fields.StringField('street')
    postalCode = fields.StringField('postalCode')
    postOfficeBox = fields.StringField('postOfficeBox')
    zarafaRemoteChangedDate = extfields.GeneralizedTimeField('zarafaRemoteChangedDate')
    zarafaRemoteId = fields.StringField('zarafaRemoteId')
    tenant = extfields.LdapToOneVirtualField(
        to_model='models_ldap.Tenant',
        up_tree=True, intermediate='ou=contacts')
