NAME := vigiconf
CONFDIR := $(SYSCONFDIR)/vigilo/$(NAME)
VARDIR := $(LOCALSTATEDIR)/lib/vigilo/$(NAME)

all: build

include buildenv/Makefile.common

build: pkg/ssh_config pkg/$(PKGNAME).cron settings.ini

pkg/ssh_config: pkg/ssh_config.in
	sed -e 's,@CONFDIR@,$(CONFDIR),' $^ > $@

pkg/$(PKGNAME).cron: pkg/cronjobs.in
	sed -e 's,@BINDIR@,$(PREFIX)/bin,' $^ > $@

settings.ini: settings.ini.in
	sed -e 's,@LOCALSTATEDIR@,$(LOCALSTATEDIR),;s,@SYSCONFDIR@,$(SYSCONFDIR),g' \
		$^ > $@

install_users:
	@echo "Creating the $(NAME) user..."
	-groupadd $(NAME)
	-useradd -s /bin/bash -M -d $(VARDIR) -g $(NAME) -c 'Vigilo VigiConf user' $(NAME)
	if [ ! -f $(CONFDIR)/ssh/vigiconf.key ]; then \
	    ssh-keygen -t rsa -f $(CONFDIR)/ssh/vigiconf.key -N "" ;\
	fi
	chown $(NAME):$(NAME) $(CONFDIR)/ssh/vigiconf.key

install: settings.ini $(PYTHON)
	$(PYTHON) setup.py install --single-version-externally-managed --root=$(DESTDIR) --record=INSTALLED_FILES
	chmod a+rX -R $(DESTDIR)$(PREFIX)/lib*/python*/*
	chmod 750 $(DESTDIR)$(VARDIR)
	# Connector
	install -p -m 755 -D pkg/init.$(DISTRO) $(DESTDIR)/etc/rc.d/init.d/vigilo-connector-vigiconf
	echo /etc/rc.d/init.d/vigilo-connector-vigiconf >> INSTALLED_FILES
	install -p -m 644 -D pkg/initconf.$(DISTRO) $(DESTDIR)$(INITCONFDIR)/vigilo-connector-vigiconf
	echo $(INITCONFDIR)/vigilo-connector-vigiconf >> INSTALLED_FILES

install_permissions:
	chown -R $(NAME):$(NAME) $(DESTDIR)$(VARDIR)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(LOCALSTATEDIR)/lock/$(PKGNAME)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(CONFDIR)

lint: lint_pylint
tests: tests_nose
clean: clean_python
	rm -f pkg/ssh_config pkg/$(PKGNAME).cron settings.ini


.PHONY: all clean install apidoc lint install_users install tests

