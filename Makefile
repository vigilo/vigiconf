NAME := vigiconf

INFILES = pkg/$(PKGNAME).cron settings.ini

all: build

include buildenv/Makefile.common.python
CONFDIR := $(SYSCONFDIR)/vigilo/$(NAME)
VARDIR := $(LOCALSTATEDIR)/lib/vigilo/$(NAME)
VIGICONFPATH = $(dir $(shell PYTHONPATH=$(DESTDIR)$(PYTHON_SITELIB) python -c 'import vigilo.vigiconf; print vigilo.vigiconf.__file__'))

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
	$(PYTHON) setup.py install --single-version-externally-managed \
		$(SETUP_PY_OPTS) --root=$(DESTDIR)

install_users:
	@echo "Creating the $(NAME) user..."
	-/usr/sbin/groupadd $(NAME)
	-/usr/sbin/useradd -s /bin/bash -M -d $(VARDIR) -g $(NAME) -c 'Vigilo VigiConf user' $(NAME)

install_permissions:
	chmod 755 $(DESTDIR)$(VARDIR)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(VARDIR)
	# Les autres utilisateurs du groupe peuvent prendre le verrou (cf. #1108).
	chmod 775 $(DESTDIR)$(LOCALSTATEDIR)/lock/$(PKGNAME)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(LOCALSTATEDIR)/lock/$(PKGNAME)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(CONFDIR)
	chmod 755 $(DESTDIR)$(VIGICONFPATH)/applications/*/*.sh

lint: lint_pylint
tests: tests_nose
doc: apidoc sphinxdoc
clean: clean_python
	rm -f $(INFILES)

prepare_sphinxdoc: bin/vigilo-autodoc
	bin/vigilo-autodoc doc/autodoc.py

sphinxdoc_html: bin/python prepare_sphinxdoc
sphinxdoc_pdf: bin/python prepare_sphinxdoc
sphinxdoc_odt: bin/python prepare_sphinxdoc

.PHONY: \
	all build clean \
	install install_users install_permissions \
	install_pkg install_python install_python_pkg \
	tests lint \
	doc apidoc \
	prepare_sphinxdoc sphinxdoc_html sphinxdoc_pdf sphinxdoc_odt \

# vim: set noexpandtab :
