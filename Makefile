NAME := vigiconf

INFILES = pkg/$(PKGNAME).cron settings.ini

all: build

include buildenv/Makefile.common.python
CONFDIR := $(SYSCONFDIR)/vigilo/$(NAME)
VARDIR := $(LOCALSTATEDIR)/lib/vigilo/$(NAME)

build: $(INFILES)

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
	-/usr/sbin/groupadd $(NAME)
	-/usr/sbin/useradd -s /bin/bash -M -d $(VARDIR) -g $(NAME) -c 'Vigilo VigiConf user' $(NAME)

install_permissions:
	chmod 755 $(DESTDIR)$(VARDIR)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(VARDIR)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(LOCALSTATEDIR)/lock/$(PKGNAME)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(CONFDIR)

lint: lint_pylint
tests: tests_nose
doc: apidoc sphinxdoc
clean: clean_python
	rm -f $(INFILES)


.PHONY: all clean install apidoc lint install_users install_permissions tests install_pkg install_python install_python_pkg
