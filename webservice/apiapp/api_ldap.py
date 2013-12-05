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


from tastypie import fields

from constants import id_help_text
from constants import isAccount_help_text
from constants import isHidden_help_text
from constants import quotaHard_help_text
from constants import quotaOverride_help_text
from constants import quotaSoft_help_text
from constants import quotaWarn_help_text
from constants import remoteChangedDate_help_text
from constants import remoteId_help_text
from constants import sendAsPrivilege_help_text
from constants import userDefaultQuotaHard_help_text
from constants import userDefaultQuotaOverride_help_text
from constants import userDefaultQuotaSoft_help_text
from constants import userDefaultQuotaWarn_help_text
from ldapresourcebase import LdapResourceBase
from models_ldap import Contact
from models_ldap import Group
from models_ldap import Server
from models_ldap import Tenant
from models_ldap import User
from tastypie_ext import extfields


DEFAULT_LIST_METHODS = ['get', 'post']
DEFAULT_DETAIL_METHODS = ['delete', 'get', 'put', 'patch']

class TenantChildMixin(object):
    '''Mix into resources that live under a tenant in the ldap tree.'''

    def get_parent(self, obj):
        return obj.tenant


class TenantResource(LdapResourceBase):
    id = fields.CharField(
        attribute='zarafaId', readonly=True, null=True, help_text=id_help_text)
    users = fields.ToManyField(
        'apiapp.api_ldap.UserResource', 'users', readonly=True, null=True,
        help_text=u'The users that belong to the tenant, referred to by their resource locations.')
    groups = fields.ToManyField(
        'apiapp.api_ldap.GroupResource', 'groups', readonly=True, null=True,
        help_text=u'The groups that belong to the tenant, referred to by their resource locations.')
    contacts = fields.ToManyField(
        'apiapp.api_ldap.ContactResource', 'contacts', readonly=True, null=True,
        help_text=u'The contacts that belong to the tenant, referred to by their resource locations.')
    name = fields.CharField(
        attribute='o', help_text=u'The name of the tenant, this is also used for display purposes. Any character is permitted.')
    isAccount = fields.BooleanField(
        attribute='zarafaAccount', null=True, help_text=isAccount_help_text)
    isHidden = fields.BooleanField(
        attribute='zarafaHidden', null=True, help_text=isHidden_help_text)
    mailDomains = fields.ListField(
        attribute='zarafaMailDomains', null=True, help_text=u'The email domains for the tenant.')
    viewPrivilege = fields.ToManyField(
        'apiapp.api_ldap.TenantResource', 'zarafaViewPrivilege', null=True,
        help_text=u'List of other tenants that are able to see this tenant in Zarafa, referred to by their resource locations.')
    adminPrivilege = fields.ToManyField(
        'apiapp.api_ldap.UserResource', 'zarafaAdminPrivilege', null=True,
        help_text=u'Users from different tenants who are administrators for this tenant.')
    systemAdmin = fields.ToOneField(
        'apiapp.api_ldap.UserResource', 'zarafaSystemAdmin', null=True,
        help_text=u'The user who is the system administrator for this tenant, referred to by his resource location.')
    quotaOverride = fields.BooleanField(
        attribute='zarafaQuotaOverride', null=True, help_text=quotaOverride_help_text)
    quotaWarn = fields.IntegerField(
        attribute='zarafaQuotaWarn', null=True, help_text=quotaWarn_help_text)
    userDefaultQuotaOverride = fields.BooleanField(
        attribute='zarafaUserDefaultQuotaOverride', null=True,
        help_text=userDefaultQuotaOverride_help_text)
    userDefaultQuotaWarn = fields.IntegerField(
        attribute='zarafaUserDefaultQuotaWarn', null=True,
        help_text=userDefaultQuotaWarn_help_text)
    userDefaultQuotaSoft = fields.IntegerField(
        attribute='zarafaUserDefaultQuotaSoft', null=True,
        help_text=userDefaultQuotaSoft_help_text)
    userDefaultQuotaHard = fields.IntegerField(
        attribute='zarafaUserDefaultQuotaHard', null=True,
        help_text=userDefaultQuotaHard_help_text)
    quotaUserWarningRecipients = fields.ToManyField(
        'apiapp.api_ldap.UserResource', 'zarafaQuotaUserWarningRecipients', null=True,
        help_text=u'List of users - referred to by their resource locations - who will recieve a notification email when a user exceeds his quota.')
    quotaCompanyWarningRecipients = fields.ToManyField(
        'apiapp.api_ldap.UserResource', 'zarafaQuotaCompanyWarningRecipients', null=True,
        help_text=u'List of users - referred to by their resource locations - who will recieve a notification email when a tenant exceeds its quota.')
    remoteChangedDate = fields.DateTimeField(
        attribute='zarafaRemoteChangedDate', null=True,
        help_text=remoteChangedDate_help_text)
    remoteId = fields.CharField(
        attribute='zarafaRemoteId', null=True, help_text=remoteId_help_text)
    companyServer = fields.ToOneField(
        'apiapp.api_ldap.ServerResource',
        attribute='zarafaCompanyServer', null=True,
        help_text=u'The resource location of the home server for the public folders of this tenant.')

    class Meta:
        detail_allowed_methods = DEFAULT_DETAIL_METHODS
        list_allowed_methods = DEFAULT_LIST_METHODS
        object_class = Tenant
        resource_name = 'tenants'


class UserResource(LdapResourceBase, TenantChildMixin):
    id = fields.CharField(
        attribute='zarafaId', readonly=True, null=True, help_text=id_help_text)
    tenant = fields.ToOneField(
        'apiapp.api_ldap.TenantResource', 'tenant',
        help_text=u'The resource location of the tenant the user belongs to.')
    groups = fields.ToManyField(
        'apiapp.api_ldap.GroupResource', 'memberOf', readonly=True, null=True,
        help_text=u'List of groups this user belongs to, referred to by their resource locations.')
    username = fields.CharField(
        attribute='uid', null=False, help_text=u'The username of the user, most commonly used for logging in.')
    password = fields.CharField(
        attribute='userPassword', null=True, help_text=u'The password of the user. The restrictions of your LDAP installation apply if you set ldap_authentication_method to bind. Usually, this field is "{MD5}"+base64(hash).')
    mail = fields.CharField(
        attribute='mail', null=True, help_text=u'The primary email address of the user. Aliases can be configured in the "aliases" attribute.')
    name = fields.CharField(
        attribute='cn', help_text=u'The full name of the user.')
    surname = fields.CharField(
        attribute='sn', help_text=u'The surname of the user.')
    aliases = fields.ListField(
        attribute='zarafaAliases', null=True, help_text=u'List of e-mail aliases for the user, not including the primary e-mail address given in "mail".')
    forwardAddress = fields.CharField(
        attribute='zarafaForwardAddress', null=True, help_text=u"The e-mail address to forward the user's email to.")
    sendAsPrivilege = fields.ToManyField(
        'apiapp.api_ldap.UserResource', 'zarafaSendAsPrivilege',
        null=True, help_text=sendAsPrivilege_help_text)
    userServer = fields.ToOneField(
        'apiapp.api_ldap.ServerResource',
        attribute='zarafaUserServer', null=False, help_text=u'The resource location of the home server for the user.')
    isAccount = fields.BooleanField(
        attribute='zarafaAccount', null=True, help_text=isAccount_help_text)
    softDeletedDate = fields.DateTimeField(
        attribute='zarafaSoftDeletedDate', null=True, readonly=True,
        help_text=u'The date this user was soft deleted, in RFC-2822 format.')
    isAdmin = fields.IntegerField(
        attribute='zarafaAdmin', null=True,
        help_text=u'A flag that indicates whether the user is a Zarafa administrator. Can be 0 (not administrator), 1 (administrator for the tenant) or 2 (administrator of the entire Zarafa cluster).')
    enabledFeatures = fields.ListField(
        attribute='zarafaEnabledFeatures', null=True,
        help_text=u'A list of features that are explicitly enabled for this user. Values can be "pop3", "imap".')
    disabledFeatures = fields.ListField(
        attribute='zarafaDisabledFeatures', null=True,
        help_text=u'A list of features that are explicitly disabled for this user. Values can be "pop3", "imap".')
    quotaOverride = fields.BooleanField(
        attribute='zarafaQuotaOverride', null=True, help_text=quotaOverride_help_text)
    quotaWarn = fields.IntegerField(
        attribute='zarafaQuotaWarn', null=True, help_text=quotaWarn_help_text)
    quotaSoft = fields.IntegerField(
        attribute='zarafaQuotaSoft', null=True, help_text=quotaSoft_help_text)
    quotaHard = fields.IntegerField(
        attribute='zarafaQuotaHard', null=True, help_text=quotaHard_help_text)
    sharedStoreOnly = fields.BooleanField(
        attribute='zarafaSharedStoreOnly', null=True,
        help_text=u'Flag that indicates whether the store is a shared store.')
    userArchiveServers = fields.ToManyField(
        'apiapp.api_ldap.ServerResource', 'zarafaUserArchiveServers', null=True,
        help_text=u'List of server resource locations that contain an archive store for the user.')
    telephoneNumber = fields.CharField(
        attribute='telephoneNumber', null=True,
        help_text=u'The telephone number of the user.')
    mobileNumber = fields.CharField(
        attribute='mobile', null=True,
        help_text=u'The mobile telephone number of the user.')
    homePhone = fields.CharField(
        attribute='homePhone', null=True,
        help_text=u'The home telephone number of the user.')
    faxNumber = fields.CharField(
        attribute='facsimileTelephoneNumber', null=True,
        help_text=u'The fax number of the user.')
    pagerNumber = fields.CharField(
        attribute='pager', null=True,
        help_text=u'The pager number of the user.')
    jpegPhoto = fields.CharField(
        attribute='jpegPhoto', null=True,
        help_text=u'A binary string representing the jpeg photo of the user.')
    description = fields.CharField(
        attribute='description', null=True,
        help_text=u'A description of the user.')
    departmentNumber = fields.CharField(
        attribute='departmentNumber', null=True,
        help_text=u'The department number of the user.')
    physicalDeliveryOfficeName = fields.CharField(
        attribute='physicalDeliveryOfficeName', null=True,
        help_text=u'The physical delivery office name of the user.')
    locality = fields.CharField(
        attribute='l', null=True, help_text=u"The name of the user's locality.")
    title = fields.CharField(
        attribute='title', null=True, help_text=u"The user's title.")
    initials = fields.CharField(
        attribute='initials', null=True, help_text=u"The user's initials")
    preferredLanguage = fields.CharField(
        attribute='preferredLanguage', null=True,
        help_text=u"The user's preferred language, indicated by its ISO-639 two-letter code.")
    employeeNumber = fields.CharField(
        attribute='employeeNumber', null=True,
        help_text=u"The user's employee number.")
    postalAddress = fields.CharField(
        attribute='postalAddress', null=True,
        help_text=u'The postal address of the user.')
    state = fields.CharField(
        attribute='st', null=True, help_text=u'The state of the user.')
    streetAddress = fields.CharField(
        attribute='street', null=True, help_text=u'The street address of the user.')
    postalCode = fields.CharField(
        attribute='postalCode', null=True, help_text=u'The postal code of the user.')
    postOfficeBox = fields.CharField(
        attribute='postOfficeBox', null=True,
        help_text=u'The post office box of the user.')
    remoteChangedDate = fields.DateTimeField(
        attribute='zarafaRemoteChangedDate', null=True,
        help_text=remoteChangedDate_help_text)
    remoteId = fields.CharField(
        attribute='zarafaRemoteId', null=True, help_text=remoteId_help_text)
    lastLogon = extfields.DateTimeField(
        lazy=True, readonly=True, null=True,
        help_text=u'The date of the last login of the user to the store in RFC-2822 format.')
    storeName = extfields.CharField(
        lazy=True, readonly=True, null=True,
        help_text=u'The name of this store in Zarafa. Typically the string [user]@[tenant].')
    storeSize = extfields.IntegerField(
        lazy=True, readonly=True, null=True, help_text=u'The store size in bytes.')

    class Meta:
        detail_allowed_methods = DEFAULT_DETAIL_METHODS
        list_allowed_methods = DEFAULT_LIST_METHODS
        object_class = User
        parent_class = TenantResource
        resource_name = 'users'

    # MAPI fields

    def dehydrate_lastLogon(self, bundle):
        store = bundle.obj.get_store()
        return store.lastLogon

    def dehydrate_storeName(self, bundle):
        store = bundle.obj.get_store()
        return store.storeName

    def dehydrate_storeSize(self, bundle):
        store = bundle.obj.get_store()
        return store.size


class GroupResource(LdapResourceBase, TenantChildMixin):
    id = fields.CharField(
        attribute='zarafaId', readonly=True, null=True, help_text=id_help_text)
    tenant = fields.ToOneField(
        'apiapp.api_ldap.TenantResource', 'tenant',
        help_text=u'The tenant the group belongs to, referred to by its resource location.')
    name = fields.CharField(
        attribute='cn', help_text=u'The name of the group.')
    members = fields.ToManyField(
        'apiapp.api_ldap.UserResource', 'member',
        null=True, help_text=u'List of members of the group, referred to by their resource locations.')
    mail = fields.CharField(
        attribute='mail', null=True, help_text=u'The primary email address of the group. Aliases can be configured in the "aliases" attribute.')
    aliases = fields.ListField(
        attribute='zarafaAliases', null=True, help_text=u'List of e-mail aliases for the group, not including the primary e-mail address given in "mail".')
    sendAsPrivilege = fields.ToManyField(
        'apiapp.api_ldap.UserResource', 'zarafaSendAsPrivilege',
        null=True, help_text=sendAsPrivilege_help_text)
    isAccount = fields.BooleanField(
        attribute='zarafaAccount', null=True, help_text=isAccount_help_text)
    isHidden = fields.BooleanField(
        attribute='zarafaHidden', null=True, help_text=isHidden_help_text)
    securityGroup = fields.BooleanField(
        attribute='zarafaSecurityGroup', null=True,
        help_text=u'If set to true, this group can also be used to set permissions on folders. Otherwise, it is only a distribution group.')
    remoteChangedDate = fields.DateTimeField(
        attribute='zarafaRemoteChangedDate', null=True,
        help_text=remoteChangedDate_help_text)
    remoteId = fields.CharField(
        attribute='zarafaRemoteId', null=True, help_text=remoteId_help_text)

    class Meta:
        detail_allowed_methods = DEFAULT_DETAIL_METHODS
        list_allowed_methods = DEFAULT_LIST_METHODS
        object_class = Group
        parent_class = TenantResource
        resource_name = 'groups'


class ContactResource(LdapResourceBase, TenantChildMixin):
    id = fields.CharField(
        attribute='zarafaId', readonly=True, null=True, help_text=id_help_text)
    tenant = fields.ToOneField(
        'apiapp.api_ldap.TenantResource', 'tenant',
        help_text=u'The resource location of the tenant the contact belongs to.')
    mail = fields.CharField(
        attribute='mail', null=True, help_text=u'The primary email address of the contact. Aliases can be configured in the "aliases" attribute.')
    name = fields.CharField(
        attribute='cn', help_text=u'The full name of the contact.')
    surname = fields.CharField(
        attribute='sn', help_text=u'The surname of the contact.')
    aliases = fields.ListField(
        attribute='zarafaAliases', null=True, help_text=u'List of e-mail aliases for the contact, not including the primary e-mail address given in "mail".')
    sendAsPrivilege = fields.ToManyField(
        'apiapp.api_ldap.UserResource', 'zarafaSendAsPrivilege',
        null=True, help_text=sendAsPrivilege_help_text)
    isAccount = fields.BooleanField(
        attribute='zarafaAccount', null=True, help_text=isAccount_help_text)
    isHidden = fields.BooleanField(
        attribute='zarafaHidden', null=True, help_text=isHidden_help_text)
    telephoneNumber = fields.CharField(
        attribute='telephoneNumber', null=True,
        help_text=u'The telephone number of the user.')
    mobileNumber = fields.CharField(
        attribute='mobile', null=True,
        help_text=u'The mobile telephone number of the contact.')
    homePhone = fields.CharField(
        attribute='homePhone', null=True,
        help_text=u'The home telephone number of the contact.')
    faxNumber = fields.CharField(
        attribute='facsimileTelephoneNumber', null=True,
        help_text=u'The fax number of the contact.')
    pagerNumber = fields.CharField(
        attribute='pager', null=True,
        help_text=u'The pager number of the contact.')
    jpegPhoto = fields.CharField(
        attribute='jpegPhoto', null=True,
        help_text=u'A binary string representing the jpeg photo of the contact.')
    description = fields.CharField(
        attribute='description', null=True,
        help_text=u'A description of the contact.')
    departmentNumber = fields.CharField(
        attribute='departmentNumber', null=True,
        help_text=u'The department number of the contact.')
    physicalDeliveryOfficeName = fields.CharField(
        attribute='physicalDeliveryOfficeName', null=True,
        help_text=u'The physical delivery office name of the contact.')
    locality = fields.CharField(
        attribute='l', null=True, help_text=u"The name of the contact's locality.")
    title = fields.CharField(
        attribute='title', null=True, help_text=u"The contact's title.")
    initials = fields.CharField(
        attribute='initials', null=True, help_text=u"The contact's initials")
    preferredLanguage = fields.CharField(
        attribute='preferredLanguage', null=True,
        help_text=u"The contact's preferred language, indicated by its ISO-639 two-letter code.")
    employeeNumber = fields.CharField(
        attribute='employeeNumber', null=True,
        help_text=u"The contact's employee number.")
    postalAddress = fields.CharField(
        attribute='postalAddress', null=True,
        help_text=u'The postal address of the contact.')
    state = fields.CharField(
        attribute='st', null=True, help_text=u'The state of the contact.')
    streetAddress = fields.CharField(
        attribute='street', null=True, help_text=u'The street address of the contact.')
    postalCode = fields.CharField(
        attribute='postalCode', null=True, help_text=u'The postal code of the contact.')
    postOfficeBox = fields.CharField(
        attribute='postOfficeBox', null=True,
        help_text=u'The post office box of the contact.')
    remoteChangedDate = fields.DateTimeField(
        attribute='zarafaRemoteChangedDate', null=True,
        help_text=remoteChangedDate_help_text)
    remoteId = fields.CharField(
        attribute='zarafaRemoteId', null=True, help_text=remoteId_help_text)

    class Meta:
        detail_allowed_methods = DEFAULT_DETAIL_METHODS
        list_allowed_methods = DEFAULT_LIST_METHODS
        object_class = Contact
        parent_class = TenantResource
        resource_name = 'contacts'


class ServerResource(LdapResourceBase):
    id = fields.CharField(
        attribute='zarafaId', readonly=True, null=True, help_text=id_help_text)
    name = fields.CharField(
        attribute='cn', help_text=u'The name of the server.')
    isAccount = fields.BooleanField(
        attribute='zarafaAccount', null=True, help_text=isAccount_help_text)
    isHidden = fields.BooleanField(
        attribute='zarafaHidden', null=True, help_text=isHidden_help_text)
    ipAddress = fields.CharField(
        attribute='ipHostNumber', help_text=u'The ip address of the server.')
    httpPort = fields.IntegerField(
        attribute='zarafaHttpPort', null=True,
        help_text=u'The HTTP port Zarafa is running under on the server.')
    sslPort = fields.IntegerField(
        attribute='zarafaSslPort', null=True,
        help_text=u'The SSL port Zarafa is running under on the server.')
    filePath = fields.CharField(
        attribute='zarafaFilePath', null=True,
        help_text=u'The Unix socket Zarafa is running under on the server.')
    containsPublic = fields.BooleanField(
        attribute='zarafaContainsPublic', null=True,
        help_text=u'Whether this server contains the public store.')
    proxyUrl = fields.CharField(
        attribute='zarafaProxyURL', null=True, help_text=u'The proxy url for this server.')

    class Meta:
        detail_allowed_methods = DEFAULT_DETAIL_METHODS
        list_allowed_methods = DEFAULT_LIST_METHODS
        object_class = Server
        resource_name = 'servers'
