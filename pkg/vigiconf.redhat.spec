%define module  vigiconf
%define name    vigilo-%{module}
%define version 2.0.0
%define release 1%{?svn}%{?dist}

%define pyver 26
%define pybasever 2.6
%define __python /usr/bin/python%{pybasever}
%define __os_install_post %{__python26_os_install_post}
%{!?python26_sitelib: %define python26_sitelib %(python26 -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:       %{name}
Summary:    Configuration manager for the supervision system
Version:    %{version}
Release:    %{release}
Source0:    %{module}.tar.bz2
URL:        http://www.projet-vigilo.org
Group:      System/Servers
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2
Buildarch:  noarch

Requires:   python26-distribute
Requires:   perl
Requires:   subversion
Requires:   openssh-clients
Requires:   tar
Requires:   libxml2-utils
Requires:   python26-argparse
Requires:   vigilo-models
Requires:   vigilo-common

Requires(pre): shadow-utils
Requires(post): openssh

######### Dependance from python dependance tree ########
Requires:   python26-argparse
Requires:   python26-babel
Requires:   python26-configobj
Requires:   python26-paste
Requires:   python26-pastedeploy
Requires:   python26-pastescript
Requires:   python26-psycopg2
Requires:   python26-distribute
Requires:   python26-sqlalchemy
Requires:   python26-transaction
Requires:   vigilo-common
Requires:   vigilo-models
Requires:   vigilo-vigiconf
Requires:   python26-zope-interface
Requires:   python26-zope.sqlalchemy
#Buildrequires: graphviz # Documentation generation

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
	PYTHON=%{__python}

%install
rm -rf $RPM_BUILD_ROOT
make install \
	DESTDIR=$RPM_BUILD_ROOT \
	PREFIX=%{_prefix} \
	SYSCONFDIR=%{_sysconfdir} \
	LOCALSTATEDIR=%{_localstatedir} \
	PYTHON=%{__python}

# Listed explicitely in %%files as %%config:
grep -v '^%{_sysconfdir}' INSTALLED_FILES \
	| grep -v '^%{_localstatedir}/lib/vigilo/%{module}' \
	> INSTALLED_FILES.filtered
mv -f INSTALLED_FILES.filtered INSTALLED_FILES

%find_lang %{name}

%pre
getent group %{module} >/dev/null || groupadd -r %{module}
getent passwd %{module} >/dev/null || \
	useradd -r -g %{module} -d %{_localstatedir}/lib/vigilo/%{module} -s /bin/bash %{module}
exit 0

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
%{_sysconfdir}/vigilo/%{module}/conf.d.example
%{_sysconfdir}/vigilo/%{module}/README.source
%config(noreplace) /etc/cron.d/*
%{_bindir}/*
%{python26_sitelib}/*
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
