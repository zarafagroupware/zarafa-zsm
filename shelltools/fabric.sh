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


FABRIC_MIN_VER="1.5.0"


fabric_detect() {
    ver=$(fab --version 2>/dev/null \
        | grep ^Fabric \
        | sed "s/Fabric \([0-9.]*\)/\1/g" \
    )

    if [[ "$ver" ]]; then
        echo "Found Fabric $ver"
        if [[ "$ver" == "${FABRIC_MIN_VER}" ]] || [[ "$ver" > "${FABRIC_MIN_VER}" ]]; then
            return 0
        fi
    fi
    return 1
}

fabric_install_deb() {
    # TODO: Check apt-cache for fabric >= 1.5?
    apt-get -y install python-pip
    apt-get -y install build-essential python-dev
    pip install Fabric
}

fabric_install_redhat() {
    if ! which easy_install >/dev/null; then
        (cd /tmp && \
            wget http://peak.telecommunity.com/dist/ez_setup.py && \
            python ez_setup.py
        )
    fi

    if ! which pip >/dev/null; then
        easy_install pip
    fi

    yum -y groupinstall "Development Tools"
    yum -y install python-devel
    pip install Fabric
}

fabric_install() {
    os=$(detect_os)

    if ! fabric_detect; then
        if [[ "$os" == "debian" ]] || [[ "$os" == "ubuntu" ]]; then
            fabric_install_deb
        elif [[ "$os" == "redhat" ]]; then
            fabric_install_redhat
        fi
    fi
}
