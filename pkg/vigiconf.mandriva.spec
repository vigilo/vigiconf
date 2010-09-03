%define module  vigiconf
%define name    vigilo-%{module}
%define version 2.0.0
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
Requires:   python-setuptools
Requires:   perl
Requires:   subversion
Requires:   openssh-clients
Requires:   tar
Requires:   libxml2-utils
Requires:   python-argparse
Requires:   vigilo-models
Requires:   vigilo-common
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
	| grep -v '^%{_localstatedir}/lib/vigilo/%{module}' \
	> INSTALLED_FILES.filtered
mv -f INSTALLED_FILES.filtered INSTALLED_FILES

%find_lang %{name}

%pre
%_pre_useradd %{module} %{_localstatedir}/lib/vigilo/%{module} /bin/bash

%post
if [ ! -f %{_sysconfdir}/vigilo/%{module}/ssh/vigiconf.key ]; then
    ssh-keygen -t rsa -f %{_sysconfdir}/vigilo/%{module}/ssh/vigiconf.key -N "" > /dev/null 2>&1 || :
fi
chown %{module}:%{module} %{_sysconfdir}/vigilo/%{module}/ssh/vigiconf.key


%clean
rm -rf $RPM_BUILD_ROOT

%files -f %{name}.lang
%defattr(-,root,root)
%doc COPYING doc/*
%dir %{_sysconfdir}/vigilo
%dir %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/
%config(noreplace) %attr(640,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/settings.ini
%config(noreplace) %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/conf.d
%config(noreplace) %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/ssh
%dir %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/new
%dir %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/prod
%{_sysconfdir}/vigilo/%{module}/conf.d.example
%{_sysconfdir}/vigilo/%{module}/README.source
%config(noreplace) /etc/cron.d/*
%{_bindir}/*
%{python_sitelib}/*
%dir %{_localstatedir}/lib/vigilo
%attr(-,%{module},%{module}) %{_localstatedir}/lib/vigilo/%{module}
%attr(-,%{module},%{module}) %{_localstatedir}/lock/vigilo-%{module}


%changelog
* Wed Aug 26 2009 Aurelien Bompard <aurelien.bompard@c-s.fr> - 1.36-3
- rebuild

* Thu Jul 30 2009 Aurelien Bompard <aurelien.bompard@c-s.fr> 1.36-2
- rename confmgr to vigiconf

* Fri Feb 06 2009 Thomas BURGUIERE <thomas.burguiere@c-s.fr>
- first creation of the RPM from debian archive