# -*- coding: utf-8 -*-
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



from libzsm.datehelper import utcnow
from libzsm.fixture_builder.base import FixtureBase
from libzsm.fixture_builder.fixture_registry import registry
from refs import *  # NOQA


class StdUser(FixtureBase):
    password = u'secret'
    isAccount = True
    isAdmin = 0
    enabledFeatures = [
        u'imap',
    ]
    disabledFeatures = [
        u'pop3',
    ]
    quotaOverride = True
    quotaWarn = 220 * 1024 ** 2
    quotaSoft = 320 * 1024 ** 2
    quotaHard = 420 * 1024 ** 2
    sharedStoreOnly = False
    userServer = server1_id
    userArchiveServers = [
        server1_id,
    ]


class Michael(StdUser):
    id = michael_id
    tenant = initech_id
    username = u'mike'
    mail = u'michael@initech.com'
    name = u'Michael Bolton'
    surname = u'Bolton'
    title = u'Mr.'
    departmentNumber = u'Z-1/4'
    physicalDeliveryOfficeName = u'Office Z'
    locality = u'Delft'
    groups = [developers_id, tpsfans_id]


class Peter(Michael):
    id = peter_id
    tenant = initech_id
    username = u'peter'
    mail = u'peter@initech.com'
    name = u'Peter Gibbons'
    surname = u'Gibbons'
    aliases = [
        u'pete@initech.com',
        u'pete@gibbons.net',
    ]
    forwardAddress = u'pete@gmail.com'
    softDeletedDate = utcnow()
    sendAsPrivilege = [michael_id]
    telephoneNumber = u'1-23456789'
    mobileNumber = u'2-23456789'
    homePhone = u'3-23456789'
    faxNumber = u'4-23456789'
    pagerNumber = u'5-23456789'
    jpegPhoto = u'aGFuaw=='
    description = u'Peter joined us from Yahoo. Sweet, Pete!'
    initials = u'H. B.'
    preferredLanguage = u'es'
    employeeNumber = u'Z9283'
    postalAddress = u'34 Downtown'
    state = u'Zuid Holland'
    streetAddress = u'34 Downtown'
    postalCode = u'0154'
    postOfficeBox = u'C35'
    lastLogon = utcnow()
    remoteChangedDate = utcnow()
    remoteId = peter_remote_id
    storeName = u'peter@initech'
    storeSize = 850


class BillLumbergh(StdUser):
    id = billlumbergh_id
    tenant = initech_id
    username = u'bill'
    password = u'secret'
    mail = u'bill@initech.com'
    name = u'Bill Lumbergh'
    surname = u'Lumbergh'


class Rene(StdUser):
    id = rene_id
    tenant = unita_id
    username = u'rené'
    surname = u'Gérard'
    name = u'René Gérard'
    description = u'中国是世界文明最早的发源地'

registry.register('users', Peter)
registry.register('users', Michael)
registry.register('users', BillLumbergh)
registry.register('users', Rene)
