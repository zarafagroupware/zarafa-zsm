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


import sys

from fabric.api import task

from models.distromodel import PkgMan
import distro
import package_manager


CMDLINE_PYTHON_RDEPS = [
    'requests',
]

REMOTESYNC_PYTHON_RDEPS = [
    'pumpkin',
    'requests',
]

WEBSERVICE_PYTHON_RDEPS = [
    'Django==1.4.5',  # <1.5   ?
    'django-tastypie==0.9.11',
    'mimeparse',
    'pumpkin',
    'six',
    'python-dateutil',
    'pygments',

    'requests',
]

LDAP_DISTRO_DEB_RDEPS = [
    'slapd',
    'ldap-utils',
]
LDAP_DISTRO_RPM_RDEPS = [
    'openldap-servers',
    'openldap-clients',
]


@task
def cmdline():
    '''Install dependencies to run the cmdline client'''
    pypkgs = CMDLINE_PYTHON_RDEPS

    package_manager.sh_pip_install(pypkgs)


@task
def ldap():
    '''Install dependencies to run the slapd server'''
    dist = distro.detect_distro()

    if dist.pkgman == PkgMan.Apt:
        pkgs = LDAP_DISTRO_DEB_RDEPS
        package_manager.sh_apt_install(pkgs)

    elif dist.pkgman == PkgMan.Yum:
        pkgs = LDAP_DISTRO_RPM_RDEPS
        package_manager.sh_yum_install(pkgs)


@task
def pkg():
    '''Install dependencies to run qa tasks'''
    dist = distro.detect_distro()

    if dist.pkgman == PkgMan.Apt:
        pkgs = [
            'dh-make',
            'dpkg-dev',
            'rpm',

            # to build python-ldap (dep pulled in by pumpkin)
            'build-essential',
            'python-dev',
            'libldap2-dev',
            'libsasl2-dev',
        ]
        package_manager.sh_apt_install(pkgs)

    elif dist.pkgman == PkgMan.Yum:
        pkgs = [
            'rpm-build',

            # to build python-ldap (dep pulled in by pumpkin)
            '"Development Tools"',
            'python-devel',
            'openldap-devel',
            'cyrus-sasl-devel',
        ]
        package_manager.sh_yum_install(pkgs)

    pypkgs = [
        'jinja2',
        'virtualenv',
    ]

    package_manager.sh_pip_install(pypkgs)


@task
def qa():
    '''Install dependencies to run qa tasks'''
    dist = distro.detect_distro()

    if dist.pkgman == PkgMan.Apt:
        pkgs = [
            'build-essential',
            'python-dev',
        ]
        package_manager.sh_apt_install(pkgs)

    elif dist.pkgman == PkgMan.Yum:
        pkgs = [
            '"Development Tools"',
            'python-devel',
        ]
        package_manager.sh_yum_install(pkgs)

    pypkgs = CMDLINE_PYTHON_RDEPS + WEBSERVICE_PYTHON_RDEPS + [
        # Development/Testing tools
        'coverage',
        'ipdbplugin',
        'nose',
        'nose-cov',
        'nose-selecttests',
        'rednose',
        'beautifulsoup4',
        'flake8',

        'ipdb',
        'ipython',
    ]

    if sys.version_info < (2, 7):
        pypkgs.extend([
            # Development/Testing tools
            'unittest2',
        ])

    package_manager.sh_pip_install(pypkgs)


@task
def webservice():
    '''Install dependencies to run the webservice'''
    dist = distro.detect_distro()

    if dist.pkgman == PkgMan.Apt:
        pkgs = [
            'build-essential',
            'python-dev',
            'libldap2-dev',
            'libsasl2-dev',

            'python-ldap',

            'libapache2-mod-wsgi',
        ]
        package_manager.sh_apt_install(pkgs)

    elif dist.pkgman == PkgMan.Yum:
        pkgs = [
            '"Development Tools"',
            'python-devel',
            'openldap-devel',
            'cyrus-sasl-devel',

            'python-ldap',

            'mod_wsgi',
        ]
        package_manager.sh_yum_install(pkgs)

    pypkgs = WEBSERVICE_PYTHON_RDEPS + [
        # Development/Testing tools
        'django-extensions',
        'ipython',
        'ipdb',
    ]

    package_manager.sh_pip_install(pypkgs)


@task
def zcp():
    '''Install dependencies to run zarafa services'''
    dist = distro.detect_distro()

    if dist.pkgman == PkgMan.Apt:
        pkgs = [
            'mysql-server',
        ]

    elif dist.pkgman == PkgMan.Yum:
        pkgs = [
            'mysql-server',
        ]
        package_manager.sh_yum_install(pkgs)


@task
def all():
    '''Install all dependencies'''
    ldap()
    zcp()
    cmdline()
    webservice()
    pkg()
    qa()
