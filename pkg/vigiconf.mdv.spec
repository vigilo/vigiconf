%define	name	vigilo-confmgr
%define	version	1.35
%define release 1

Name:		%{name}
Summary:	Configuration manager for the supervision system
Version:	%{version}
Release:	%{release}
Source0:	ConfMgr.tar.bz2

Group:		System/Servers
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-build
License:	GPLv2
#Copyright:	CS-SI
Requires:	python >= 2.5
Requires:	perl
Requires:	subversion
Requires:	openssh-clients
Requires:	tar
Requires:	sec
Buildrequires:	graphviz
Buildarch:	noarch

%description
Configuration manager for the supervision system
This program generates and pushes the configuration for the
applications used in the supervision system.
This application is part of the Vigilo Project <http://vigilo-project.org>

%prep
%setup -q -n ConfMgr


%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT INITCONFDIR=/etc/sysconfig install 
make DESTDIR=$RPM_BUILD_ROOT INITCONFDIR=/etc/sysconfig install_docs

%pre
echo "Creating the confmgr user..." >/dev/null 2>&1
groupadd confmgr >/dev/null 2>&1 || :
useradd -s /bin/bash -m -d /home/confmgr -g confmgr -c 'ConfMgr user' confmgr >/dev/null 2>&1 || :


%post

%preun

%postun

%clean

%files
%defattr(-,root,root)
%doc COPYING
%doc %{_datadir}/docs/confmgr/
%{_datadir}/confmgr/
#%attr(0640,confmgr,confmgr)%{_sysconfdir}/confmgr/
#%attr(0640,confmgr,confmgr,750)%{_sysconfdir}/confmgr/
%attr(-,confmgr,confmgr)%{_sysconfdir}/confmgr/
%{_sysconfdir}/cron.d/*
%attr(-,confmgr,confmgr)/var/lock/confmgr/
%_bindir/confmgr
%_bindir/discoverator
%_sbindir/dispatchator
%attr(-,confmgr,confmgr)/var/lib/confmgr


%changelog
* Fri Feb 06 2009 Thomas BURGUIERE <thomas.burguiere@c-s.fr>
- first creation of the RPM from debian archive
