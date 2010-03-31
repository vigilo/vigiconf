%define module  vigiconf
%define name    vigilo-%{module}
%define version 1.37
%define release 1%{?svn}

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
Requires:   libxml2-utils
Requires:   vigilo-models
# Pour CorrTrap
Requires:   sec
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
make \
	PREFIX=%{_prefix} \
	SYSCONFDIR=%{_sysconfdir} \
	LOCALSTATEDIR=%{_localstatedir} \
	PYTHON=%{_bindir}/python

%install
rm -rf $RPM_BUILD_ROOT
make install \
	DESTDIR=$RPM_BUILD_ROOT \
	PREFIX=%{_prefix} \
	SYSCONFDIR=%{_sysconfdir} \
	LOCALSTATEDIR=%{_localstatedir} \
	PYTHON=%{_bindir}/python

# Listed explicitely in %%files as %%config:
grep -v '^%{_sysconfdir}' INSTALLED_FILES \
	| grep -v '^%{_localstatedir}/lib/vigilo/vigiconf' \
	> INSTALLED_FILES.filtered
mv -f INSTALLED_FILES.filtered INSTALLED_FILES


%pre
groupadd vigiconf >/dev/null 2>&1 || :
useradd -s /bin/bash -M -d / -g vigiconf -c 'Vigilo VigiConf user' vigiconf >/dev/null 2>&1 || :

%post
if [ ! -f %{_sysconfdir}/vigilo/vigiconf/ssh/vigiconf.key ]; then
    ssh-keygen -t rsa -f %{_sysconfdir}/vigilo/vigiconf/ssh/vigiconf.key -N "" > /dev/null 2>&1 || :
fi
chown vigiconf:vigiconf %{_sysconfdir}/vigilo/vigiconf/ssh/vigiconf.key


%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc COPYING doc/*
%dir %{_sysconfdir}/vigilo
%dir %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo/vigiconf/
%config(noreplace) %attr(640,vigiconf,vigiconf) %{_sysconfdir}/vigilo/vigiconf/settings.ini
%config(noreplace) %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo/vigiconf/conf.d
%config(noreplace) %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo/vigiconf/ssh
%dir %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo/vigiconf/new
%dir %attr(-,vigiconf,vigiconf) %{_sysconfdir}/vigilo/vigiconf/prod
%{_sysconfdir}/vigilo/vigiconf/conf.d.example
%{_sysconfdir}/vigilo/vigiconf/README.source
%config(noreplace) /etc/cron.d/*
%dir %{_localstatedir}/lib/vigilo
%attr(-,vigiconf,vigiconf) %{_localstatedir}/lib/vigilo/vigiconf
%attr(-,vigiconf,vigiconf) %{_localstatedir}/lock/vigilo-vigiconf


%changelog
* Wed Aug 26 2009 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.36-3
- rebuild

* Thu Jul 30 2009 Aurelien Bompard <aurelien.bompard@c-s.fr> 1.36-2
- rename confmgr to vigiconf

* Fri Feb 06 2009 Thomas BURGUIERE <thomas.burguiere@c-s.fr>
- first creation of the RPM from debian archive
