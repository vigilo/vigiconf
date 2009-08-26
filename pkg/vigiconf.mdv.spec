%define module  vigiconf
%define name    vigilo-%{module}
%define version 1.36
%define release 3

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
Requires:   sec
Requires:   libxml2-utils
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

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install 


%pre
groupadd vigiconf >/dev/null 2>&1 || :
useradd -s /bin/bash -m -d /var/lib/vigilo-vigiconf -g vigiconf -c 'VigiConf user' vigiconf >/dev/null 2>&1 || :


%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc COPYING doc/*
%{_bindir}/vigiconf
%{_bindir}/vigiconf-discoverator
%{_sbindir}/vigiconf-dispatchator
%{_datadir}/vigilo-vigiconf/
%config(noreplace) %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo-vigiconf/
%config(noreplace) %{_sysconfdir}/cron.d/*
%attr(-,vigiconf,vigiconf) /var/lock/vigilo-vigiconf/
%attr(-,vigiconf,vigiconf) /var/lib/vigilo-vigiconf


%changelog
* Wed Aug 26 2009 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.36-3
- rebuild

* Thu Jul 30 2009 Aurelien Bompard <aurelien.bompard@c-s.fr> 1.36-2
- rename confmgr to vigiconf

* Fri Feb 06 2009 Thomas BURGUIERE <thomas.burguiere@c-s.fr>
- first creation of the RPM from debian archive
