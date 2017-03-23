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

#Buildrequires: graphviz # Documentation generation
BuildRequires:   python-babel

Requires:   python >= 2.5
Requires:   python-setuptools
Requires:   python-lxml
Requires:   perl
Requires:   subversion >= 1.5.6
Requires:   tar
Requires:   libxml2-utils
Requires:   python-argparse
Requires:   vigilo-models
Requires:   vigilo-common
Requires:   net-snmp-utils
Requires:   sqlite3-tools
Requires:   python-multiprocessing
Requires:   python-initgroups
######### Dependance from python dependance tree ########
Requires:   python-argparse
Requires:   python-babel
Requires:   python-configobj
Requires:   python-paste
Requires:   python-pastedeploy
Requires:   python-pastescript
Requires:   python-psycopg2
Requires:   python-setuptools
Requires:   python-sqlalchemy
Requires:   python-transaction
Requires:   vigilo-common
Requires:   vigilo-models
Requires:   vigilo-vigiconf
Requires:   python-zope-interface
Requires:   python-zope.sqlalchemy
Requires:   python-lxml

Requires(pre): rpm-helper


%description
@DESCRIPTION@
This application is part of the Vigilo Project <http://vigilo-project.org>

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

%find_lang %{name}

%pre
%_pre_useradd %{module} %{_localstatedir}/lib/vigilo/%{module} /bin/bash

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
%attr(775,%{module},%{module}) %{_localstatedir}/lock/subsys/vigilo-%{module}


%changelog
* Thu Apr 07 2011 Aurelien Bompard <aurelien.bompard@c-s.fr>
- Adapt to Vigilo V2
