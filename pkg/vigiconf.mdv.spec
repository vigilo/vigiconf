%define name    vigilo-confmgr
%define version 1.35
%define release 1

Name:       %{name}
Summary:    Configuration manager for the supervision system
Version:    %{version}
Release:    %{release}
Source0:    vigiconf.tar.bz2
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
Buildrequires: graphviz
Buildarch:  noarch

%description
Configuration manager for the supervision system
This program generates and pushes the configuration for the
applications used in the supervision system.
This application is part of the Vigilo Project <http://vigilo-project.org>

%prep
%setup -q -n vigiconf

%build

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install 


%pre
groupadd confmgr >/dev/null 2>&1 || :
useradd -s /bin/bash -m -d /home/confmgr -g confmgr -c 'ConfMgr user' confmgr >/dev/null 2>&1 || :


%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc COPYING doc/*
%{_bindir}/confmgr
%{_bindir}/discoverator
%{_sbindir}/dispatchator
%{_datadir}/vigilo-confmgr/
%config(noreplace) %attr(-,confmgr,confmgr) %{_sysconfdir}/confmgr/
%config(noreplace) %{_sysconfdir}/cron.d/*
%attr(-,confmgr,confmgr) /var/lock/vigilo-confmgr/
%attr(-,confmgr,confmgr) /var/lib/vigilo-confmgr


%changelog
* Fri Feb 06 2009 Thomas BURGUIERE <thomas.burguiere@c-s.fr>
- first creation of the RPM from debian archive
