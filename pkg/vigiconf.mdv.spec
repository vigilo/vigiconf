%define module  vigiconf
%define name    vigilo-%{module}
%define version 1.36
%define release 4

Name:       %{name}
Summary:    Configuration manager for the supervision system
Version:    %{version}
Release:    %{release}
Source0:    %{module}.tar.bz2
URL:        http://www.projet-vigilo.org
Group:      System/Servers
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2
Requires:   python >= 2.5
Requires:   perl
Requires:   subversion
Requires:   openssh-clients
Requires:   tar
#Requires:   sec
Requires:   libxml2-utils
Requires:   vigilo-models
#Buildrequires: graphviz # Documentation generation
Buildarch:  noarch

# Renamed from vigilo-confmgr
Obsoletes:  vigilo-confmgr < 1.36-2
Provides:   vigilo-confmgr = %{version}-%{release}


%description
This program generates and pushes the configuration for the
applications used in the supervision system.
This application is part of the Vigilo Project <http://vigilo-project.org>

%prep
%setup -q -n %{module}

%build
make PREFIX=%{_prefix} SYSCONFDIR=%{_sysconfdir} LOCALSTATEDIR=%{_localstatedir}

%install
rm -rf $RPM_BUILD_ROOT
make install DESTDIR=$RPM_BUILD_ROOT PREFIX=%{_prefix} SYSCONFDIR=%{_sysconfdir} LOCALSTATEDIR=%{_localstatedir}
# Listed explicitely in %%files as %%config:
grep -v '^%{_sysconfdir}' INSTALLED_FILES \
	| grep -v '^%{_localstatedir}/lib/vigilo-vigiconf' \
	> INSTALLED_FILES.filtered
mv -f INSTALLED_FILES.filtered INSTALLED_FILES


%pre
groupadd vigiconf >/dev/null 2>&1 || :
useradd -s /bin/bash -m -d /var/lib/vigilo-vigiconf -g vigiconf -c 'VigiConf user' vigiconf >/dev/null 2>&1 || :


%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc COPYING doc/*
%dir %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo-vigiconf/
%config(noreplace) %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo-vigiconf/settings.py
%config(noreplace) %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo-vigiconf/conf.d
%dir %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo-vigiconf/new
%dir %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo-vigiconf/prod
%{_sysconfdir}/vigilo-vigiconf/conf.d.example
%{_sysconfdir}/vigilo-vigiconf/README.source
%config(noreplace) %{_sysconfdir}/cron.d/*
%dir %attr(-,vigiconf,vigiconf) %{_localstatedir}/lib/vigilo-vigiconf
%dir %attr(-,vigiconf,vigiconf) %{_localstatedir}/lib/vigilo-vigiconf/db
%config(noreplace) %attr(-,vigiconf,vigiconf) %{_localstatedir}/lib/vigilo-vigiconf/db/ssh_config
%attr(-,vigiconf,vigiconf) %{_localstatedir}/lib/vigilo-vigiconf/deploy
%attr(-,vigiconf,vigiconf) %{_localstatedir}/lib/vigilo-vigiconf/revisions


%changelog
* Wed Aug 26 2009 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.36-3
- rebuild

* Thu Jul 30 2009 Aurelien Bompard <aurelien.bompard@c-s.fr> 1.36-2
- rename confmgr to vigiconf

* Fri Feb 06 2009 Thomas BURGUIERE <thomas.burguiere@c-s.fr>
- first creation of the RPM from debian archive
