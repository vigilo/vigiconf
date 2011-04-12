NAME := vigiconf
CONFDIR := $(SYSCONFDIR)/vigilo/$(NAME)
VARDIR := $(LOCALSTATEDIR)/lib/vigilo/$(NAME)

INFILES = pkg/ssh_config pkg/$(PKGNAME).cron settings.ini

all: build

include buildenv/Makefile.common

build: $(INFILES)

pkg/ssh_config: pkg/ssh_config.in
	sed -e 's,@CONFDIR@,$(CONFDIR),' $^ > $@

pkg/$(PKGNAME).cron: pkg/cronjobs.in
	sed -e 's,@BINDIR@,$(PREFIX)/bin,' $^ > $@

settings.ini: settings.ini.in
	sed -e 's,@LOCALSTATEDIR@,$(LOCALSTATEDIR),;s,@SYSCONFDIR@,$(SYSCONFDIR),g' \
		$^ > $@

install: build install_python install_users install_permissions
install_pkg: build install_python_pkg

install_python: settings.ini $(PYTHON)
	$(PYTHON) setup.py install --record=INSTALLED_FILES
install_python_pkg: settings.ini $(PYTHON)
	$(PYTHON) setup.py install --single-version-externally-managed --root=$(DESTDIR)

install_users:
	@echo "Creating the $(NAME) user..."
	-groupadd $(NAME)
	-useradd -s /bin/bash -M -d $(VARDIR) -g $(NAME) -c 'Vigilo VigiConf user' $(NAME)
	if [ ! -f $(DESTIDR)$(CONFDIR)/ssh/vigiconf.key ]; then \
	    ssh-keygen -t rsa -f $(DESTIDR)$(CONFDIR)/ssh/vigiconf.key -N "" ;\
	fi
	chown $(NAME):$(NAME) $(DESTIDR)$(CONFDIR)/ssh/vigiconf.key

install_permissions:
	chmod 750 $(DESTDIR)$(VARDIR)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(VARDIR)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(LOCALSTATEDIR)/lock/$(PKGNAME)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(CONFDIR)

lint: lint_pylint
tests: tests_nose
clean: clean_python
	rm -f $(INFILES)


.PHONY: all clean install apidoc lint install_users install_permissions tests install_pkg install_python install_python_pkg
