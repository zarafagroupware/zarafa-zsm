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


from os.path import dirname
from os.path import abspath
from os.path import join
import logging
import os
import re

from django import template
from django.utils.safestring import mark_safe

from apiapp.resourcebase import ResourceBase

import syntax_tags

logger = logging.getLogger(__file__)
register = template.Library()


@register.filter
def format_template_url(value):
    value = re.sub('([{].*?[}])', '<em class="blue">\g<1></em>', value)
    return mark_safe(value)


def render_boolean(value):
    if value:
        value = u'<em class="green">{0}</em>'.format(u'Yes')
    else:
        value = u'<em class="red">{0}</em>'.format(u'No')
    return mark_safe(value)


@register.inclusion_tag('apiapp/includes/doc_fields.html')
def render_fields(resource=None):
    assert isinstance(resource, ResourceBase)

    schema = resource.build_schema()['fields']

    rows = []
    for field_name, field_object in sorted(resource.fields.items()):

        example = schema[field_name].get('example')
        help_text = schema[field_name].get('help_text')
        lazy = schema[field_name].get('lazy')
        nullable = schema[field_name].get('nullable')
        read_only = schema[field_name].get('readonly')
        signature = schema[field_name].get('signature', u'')
        type = schema[field_name].get('type')

        example = resource.serialize(None, example, 'application/json')

        # NOTE: dirty camelize fix applied to the schema
        if field_name == 'resource_uri':
            field_name = 'resourceUri'

        dct = dict(
            name=field_name,
            example=example,
            help_text=help_text,
            lazy=render_boolean(lazy),
            nullable=render_boolean(nullable),
            read_only=render_boolean(read_only),
            signature=signature,
            type=type,
        )
        rows.append(dct)

    return {
        'fields': rows,
    }


_code_cache = {}
_rx_vim_modeline = re.compile('(?m)^\s*//\s*vim?.*$')

@register.simple_tag
def load_code(path):
    global _code_cache
    global _rx_vim_modeline

    _, ext = os.path.splitext(path)
    lang = ext.replace('.', '')

    content = _code_cache.get(path, '')
    if not content:
        base = abspath(join(dirname(__file__), '..', 'templates', 'apiapp'))
        fp = join(base, path)

        try:
            content = open(fp, 'rt').read()
            if lang in ['js', 'json']:
                content = _rx_vim_modeline.sub('', content)
                content = content.strip()

            _code_cache[path] = content
        except IOError:
            logger.exception(u'Failed to load code from path {0}'.format(fp))

    content = syntax_tags.format_code(content, lang)

    return content
