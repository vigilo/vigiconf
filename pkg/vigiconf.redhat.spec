%define module  @SHORT_NAME@

%define pyver 26
%define pybasever 2.6
%define __python /usr/bin/python%{pybasever}
%define __os_install_post %{__python26_os_install_post}
%{!?python26_sitelib: %define python26_sitelib %(python26 -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:       vigilo-%{module}
Summary:    @SUMMARY@
Version:    @VERSION@
Release:    @RELEASE@%{?dist}
Source0:    %{name}-%{version}.tar.gz
URL:        @URL@
Group:      System/Servers
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-build
License:    GPLv2
Buildarch:  noarch

Buildrequires: python26-distribute
#Buildrequires: graphviz # Documentation generation

Requires:   python26-distribute
Requires:   python26-lxml
Requires:   perl
Requires:   subversion
Requires:   openssh-clients
Requires:   tar
Requires:   libxml2
Requires:   python26-argparse
Requires:   vigilo-models
Requires:   vigilo-common
Requires:   net-snmp-utils
Requires:   sqlite >= 3
Requires:   python26-initgroups

Requires(pre): shadow-utils
Requires(post): openssh

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
%defattr(644,root,root,755)
%doc COPYING.txt README.txt doc/*
%dir %{_sysconfdir}/vigilo
%dir %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/
%config(noreplace) %attr(640,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/settings.ini
%config(noreplace) %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/conf.d
%config(noreplace) %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/ssh
%dir %attr(-,%{module},%{module}) %{_sysconfdir}/vigilo/%{module}/plugins
%{_sysconfdir}/vigilo/%{module}/conf.d.example
%{_sysconfdir}/vigilo/%{module}/README.post-install
%config(noreplace) /etc/cron.d/*
%attr(755,root,root) %{_bindir}/*
%{python26_sitelib}/*
%dir %{_localstatedir}/lib/vigilo
%attr(-,%{module},%{module}) %{_localstatedir}/lib/vigilo/%{module}
%attr(-,%{module},%{module}) %{_localstatedir}/lock/vigilo-%{module}


%changelog
* Thu Apr 07 2011 Aurelien Bompard <aurelien.bompard@c-s.fr> 
- Adapt to Vigilo V2
