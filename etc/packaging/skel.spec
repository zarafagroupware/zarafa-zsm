Summary: <description>
Name: <name>
Version: <version>
Release: <release>
License: <license>
Group: <license>
BuildArch: <arch>
Source: <source_url>
BuildRoot: /var/tmp/%{name}-buildroot
Requires: <deps>

%description
<desc>

%prep
%setup -q

%build
make RPM_OPT_FLAGS="$RPM_OPT_FLAGS"

%install
make DESTDIR="$RPM_BUILD_ROOT" install

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)

<files>

%changelog
