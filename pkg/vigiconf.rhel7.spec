%define module  @SHORT_NAME@

Name:       vigilo-%{module}
Summary:    @SUMMARY@
Version:    @VERSION@
Release:    @RELEASE@%{?dist}
Source0:    %{name}-%{version}.tar.gz
URL:        @URL@
Group:      Applications/System
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2
Buildarch:  noarch

Buildrequires: python-distribute
#Buildrequires: graphviz # Documentation generation
BuildRequires:   python-babel

Requires:   python-distribute
Requires:   python-lxml >= 3.0.1
Requires:   perl
Requires:   subversion >= 1.5.6
Requires:   tar
Requires:   libxml2
Requires:   python-argparse
Requires:   vigilo-models
Requires:   vigilo-common
Requires:   net-snmp-utils
Requires:   sqlite >= 3
Requires:   python-initgroups
Requires:   python-netifaces

Requires(pre): shadow-utils

%description
@DESCRIPTION@
This application is part of the Vigilo Project <http://vigilo-nms.com>

%prep
%setup -q

%build

%install
rm -rf $RPM_BUILD_ROOT
make install_pkg \
    DESTDIR=$RPM_BUILD_ROOT \
    PREFIX=%{_prefix} \
    SYSCONFDIR=%{_sysconfdir} \
    LOCALSTATEDIR=%{_localstatedir} \
    PYTHON=%{__python}
mkdir -p $RPM_BUILD_ROOT/%{_tmpfilesdir}
install -m 644 pkg/%{name}.conf $RPM_BUILD_ROOT/%{_tmpfilesdir}

%find_lang %{name}

%pre
getent group %{module} >/dev/null || groupadd -r %{module}
getent passwd %{module} >/dev/null || \
    useradd -r -g %{module} -d %{_localstatedir}/lib/vigilo/%{module} -s /bin/bash %{module}
exit 0

%post
%tmpfiles_create %{_tmpfilesdir}/%{name}.conf

%clean
rm -rf $RPM_BUILD_ROOT

%files -f %{name}.lang
%defattr(644,root,root,755)
%doc COPYING.txt README.txt doc/*
%dir %{_sysconfdir}/vigilo
%dir %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/
%config(noreplace) %attr(640,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/settings.ini
%config(noreplace) %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/conf.d
%dir %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/plugins
%{_sysconfdir}/vigilo/%{module}/conf.d.example
%{_sysconfdir}/vigilo/%{module}/README.post-install
%config(noreplace) /etc/cron.d/*
%attr(755,root,root) %{_bindir}/*
%{python_sitelib}/*
%attr(755,root,root) %{python_sitelib}/vigilo/%{module}/applications/*/*.sh
%dir %{_localstatedir}/lib/vigilo
%attr(-,%{module},%{module}) %{_localstatedir}/lib/vigilo/%{module}
# Les autres utilisateurs du groupe peuvent prendre le verrou (cf. #1108).
%attr(644,root,root) %{_tmpfilesdir}/%{name}.conf


%changelog
* Thu Mar 23 2017 Yves Ouattara <yves.ouattara@c-s.fr>
- Rebuild for RHEL7.

* Fri Jan 21 2011 Vincent Quéméner <vincent.quemener@c-s.fr>
- Rebuild for RHEL6.
