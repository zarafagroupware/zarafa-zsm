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


import logging

from tastypie.authorization import Authorization
from tastypie.http import HttpForbidden

from permissions import resolve
import ldapmodelbase

logger = logging.getLogger(__name__)


class LdapAuthorization(Authorization):
    def __init__(self, resource_obj):
        super(LdapAuthorization, self).__init__()

        self.resource_obj = resource_obj

    def is_authorized(self, request, object=None):
        # map request -> permission
        perm, match = resolve(request, self.resource_obj)
        logger.info(u'perm: {0:22}  {1:8}  {2}'.format(
            getattr(perm, 'name', '-------------'), request.method, request.get_full_path(),
        ))

        if perm:
            if perm.is_priv:
                return self.check_privilege(request, perm)
            else:
                return self.check_acl(request, match, perm)

        return self.reject_access()

    def check_acl(self, request, match, perm):
        res = perm.resource
        if perm.resource.parent:
            res = perm.resource.parent

        model = res._meta.object_class
        if issubclass(model, ldapmodelbase.ModelBase):

            id = match.kwargs.get(res.get_uri_pk_group_name())
            obj = model.get_object(getattr(model, 'zarafaId'), id)

            if obj:
                try:
                    if not request.user.has_perm(perm, obj):
                        return self.reject_access(perm)
                # XXX handle lookup on object without a zarafaACL property
                except AttributeError:
                    return True

        return True  # XXX

    def check_privilege(self, request, perm):
        if request.user.has_perm(perm):
            return True

        return self.reject_access(perm)

    def reject_access(self, perm=None):
        json = ''

        if perm:
            resp = {
                'permissionDenied': perm.name,
            }
            json = self.resource_obj._meta.serializer.to_json(resp)

        return HttpForbidden(json, mimetype='application/json')
