%define name rgwadmin
%define unmangled_name rgwadmin
%define release 1

Summary: Python Rados Gateway Admin API
Name: %{python}-%{name}
Version: %{version}
Release: %{release}
Source0: %{unmangled_name}-%{version}.tar.gz
License: LGPL v2.1
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{unmangled_name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: UMIACS Staff <github@umiacs.umd.edu>
Requires: python3
Requires: python3-requests
Requires: python3-requests-aws
Url: https://github.com/UMIACS/rgwadmin

%description
rgwadmin is a Python library to access the Ceph Object Storage Admin API.

%prep
%setup -n %{unmangled_name}-%{version}

%build
%{python} setup.py build

%install
%{python} setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
