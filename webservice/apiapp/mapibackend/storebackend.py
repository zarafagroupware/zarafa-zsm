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


try:
    from MAPI import Tags as tags
    from MAPI.Util import GetDefaultStore
    from MAPI.Util import OpenECSession
    from MAPI.Util.Generators import GetStores
    from MAPI.Util.AddressBook import GetUserList

    from mapiobject import MapiObject
except:
    print("Failed to import MAPI!!!")

import logging

from apiapp.loaders.models import get_model
from apiapp.models_mapi import Store
from conf.settings import config
from debug import lookup_propvalue_key
import exc

logger = logging.getLogger(__file__)


def binguid_to_hexstr(value):
    return value.encode('hex')


class StoreBackend(object):
    _instance = None

    @classmethod
    def get(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    def get_session(self, server=None):
        kwargs = {}

        socket = config.ZARAFA_SOCKET
        if server:
            socket = 'https://{0}:{1}/'.format(server.ipHostNumber,
                                               server.zarafaSslPort)

        if socket.startswith('https://'):
            kwargs.update(dict(
                sslkey_file=config.ZARAFA_SSLKEY_FILE,
                sslkey_pass=config.ZARAFA_SSLKEY_PASS,
            ))

        session = OpenECSession(
            config.ZARAFA_ADMIN_USERNAME,
            config.ZARAFA_ADMIN_PASSWORD,
            socket,
            **kwargs
        )

        return session

    @property
    def session(self):
        if not getattr(self, '_session', None):
            self._session = self.get_session()
        return self._session

    def get_service_admin(self):
        store = GetDefaultStore(self.session)
        service_admin = store.QueryInterface(tags.IID_IECServiceAdmin)
        return service_admin

    def sync_users(self):
        service_admin = self.get_service_admin()
        service_admin.SyncUsers(None)

    def get_stores(self):
        stores = GetStores(self.session)

        lst = []
        for imsgstore in stores:
            model = self._get_store_model(imsgstore)
            lst.append(model)

        return lst

    def get_tenant_stores_orig(self, tenant):
        userids = GetUserList(self.session, companyname=tenant.o,
                              flags=tags.MAPI_UNICODE)
        stores = []
        for userid in userids:
            store = self.get_user_store(userid=userid)
            stores.append(store)
        return stores

    def get_tenant_stores(self, tenant):
        # uses GetMailboxTable to list stores then open each IMsgStore
        store = GetDefaultStore(self.session)
        iems = store.QueryInterface(tags.IID_IExchangeManageStore)
        table = iems.GetMailboxTable(None, 0)

        # FIXME: set a filter on the table to filter by tenant,
        # needs ZCP support: ZCP-11417

        table.SetColumns([
            tags.PR_DISPLAY_NAME_W,
            tags.PR_EC_COMPANYID,
            tags.PR_EC_COMPANY_NAME_W,
            tags.PR_EC_STOREGUID,
            tags.PR_EC_STORETYPE,
            tags.PR_MESSAGE_SIZE_EXTENDED,
            tags.PR_STORE_ENTRYID,
            tags.PR_EC_USERNAME_W,
            tags.PR_ENTRYID,
        ], 0)

        stores = []

        rows = table.QueryRows(-1, 0)
        for row in rows:
            from debug import pprint_propvaluelist
            #pprint_propvaluelist(row)

            entryId = row[6].Value
            st = self.session.OpenMsgStore(0, entryId, tags.IID_IMsgStore, tags.MDB_WRITE)
            try:
                store = self._get_store_model(st)
                # filter by tenant since there is no way to filter the table earlier
                if tenant.zarafaId == store.tenant.zarafaId:
                    stores.append(store)

                #store.tenant = tenant
            except Exception as e:
                pass
                #print e

        return stores

    def get_tenant_stores_exh_(self, tenant):
        # deprecated:
        # uses OpenUserStoresTable, no way to get an IMsgStore from there,
        # cannot open using tags.PR_STORE_ENTRYID
        '''List all stores for tenant, including orphans.'''
        service_admin = self.get_service_admin()

        table = service_admin.OpenUserStoresTable(tags.MAPI_UNICODE)
        table.SetColumns([
            tags.PR_DISPLAY_NAME_W,
            tags.PR_EC_COMPANYID,
            tags.PR_EC_COMPANY_NAME_W,
            tags.PR_EC_STOREGUID,
            tags.PR_EC_STORETYPE,
            tags.PR_MESSAGE_SIZE_EXTENDED,
            tags.PR_STORE_ENTRYID,
            #tags.PR_EC_USERNAME_W,
            #tags.PR_ENTRYID,
        ], 0)
        cnt = table.GetRowCount(0)
        rows = table.QueryRows(cnt, 0)

        stores = []
        matched_rows = []

        for row in rows:

            entryId = row[6].Value
            from debug import pprint_propvaluelist
            pprint_propvaluelist(row)
            self.session.OpenMsgStore(0, entryId, tags.IID_IMsgStore, tags.MDB_WRITE)

            items = row
            for item in items:
                key = lookup_propvalue_key(item)
                if key == tags.PR_EC_COMPANY_NAME_W:
                    if tenant.o == item.Value:
                        matched_rows.append(row)

        model = get_model('models_ldap.User')
        for row in matched_rows:
            user = model.get_by_userid(row[0].Value)
            dct = dict(
                lastLogon=None,
                size=row[5].Value,
                zarafaId=binguid_to_hexstr(row[3].Value),
                tenant=tenant,
                user=user,
                userId=row[0].Value,
            )

            store = Store(initial=dct)
            stores.append(store)

        return stores

    def get_store(self, id):
        stores = GetStores(self.session)

        for imsgstore in stores:
            storemodel = MapiObject(imsgstore, dict(guid=tags.PR_RECORD_KEY))
            if binguid_to_hexstr(storemodel.guid) == id:
                return self._get_store_model(imsgstore)

        raise exc.StoreNotFound

    def get_user_store(self, userid):
        imsgstore = self._find_user_store(userid)

        if not imsgstore:
            try:
                model = get_model('models_ldap.User')
                user = model.get_by_userid(userid)
                session = self.get_session(user.zarafaUserServer)

                store = GetDefaultStore(session)
                service_admin = store.QueryInterface(tags.IID_IECServiceAdmin)
                userEntryId = service_admin.ResolveUserName(userid, tags.MAPI_UNICODE)
                service_admin.CreateStore(tags.ECSTORE_TYPE_PRIVATE, userEntryId)
            except Exception as e:
                logger.exception(e)

            imsgstore = self._find_user_store(userid)

        return self._get_store_model(imsgstore)

    def _find_user_store(self, userid):
        userid = str(userid) # XXX GetStores doesn't accept unicode userid as of 7.1.6
        stores = GetStores(self.session, users=userid, flags=tags.MAPI_UNICODE)
        imsgstore = None
        try:
            imsgstore = stores.next()
        except StopIteration:
            pass
        return imsgstore

    def _get_store_model(self, imsgstore):
        dct = {}

        props = dict(
            size=tags.PR_MESSAGE_SIZE_EXTENDED,
            guid=tags.PR_RECORD_KEY,
            lastLogon=tags.PR_LAST_LOGON_TIME,
            userEntryId=tags.PR_MAILBOX_OWNER_ENTRYID,
        )

        storemodel = MapiObject(imsgstore, props)
        dct.update(dict(
            lastLogon=storemodel.lastLogon,
            size=storemodel.size,
            zarafaId=binguid_to_hexstr(storemodel.guid),
        ))

        if storemodel.userEntryId:
            imailuser = self.session.OpenEntry(storemodel.userEntryId, None, 0)
            usermodel = MapiObject(imailuser, dict(userid=tags.PR_ACCOUNT_W))

            dct.update(dict(
                storeName=usermodel.userid,
            ))

        return Store(initial=dct)
