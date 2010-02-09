NAME := vigiconf
PKGNAME = vigilo-$(NAME)
PYTHON = python
PREFIX = /usr
SYSCONFDIR = /etc
LOCALSTATEDIR = /var
CONFDIR = $(SYSCONFDIR)/$(PKGNAME)
VARDIR = $(LOCALSTATEDIR)/lib/$(PKGNAME)
DESTDIR = 

all:
	sed -e 's,@VIGILODIR@,$(VARDIR),' pkg/ssh_config.in > pkg/ssh_config
	touch --reference pkg/ssh_config.in pkg/ssh_config
	sed -e 's,@BINDIR@,$(PREFIX)/bin,' pkg/cronjobs.in > pkg/$(PKGNAME).cron
	touch --reference pkg/cronjobs.in pkg/$(NAME).cron
	python setup.py build

install_users:
	@echo "Creating the $(NAME) user..."
	-groupadd $(NAME)
	-useradd -s /bin/bash -m -d $(VARDIR) -g $(NAME) -c 'VigiConf user' $(NAME)

install:
	python setup.py install --single-version-externally-managed --root=$(DESTDIR) --record=INSTALLED_FILES
	chmod 750 $(DESTDIR)$(VARDIR)

install_permissions:
	chown -R $(NAME):$(NAME) $(DESTDIR)$(VARDIR)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(CONFDIR)



include ../glue/Makefile.common
lint: lint_pylint
tests: tests_nose
clean: clean_python
	rm -f pkg/ssh_config pkg/$(PKGNAME).cron


.PHONY: all clean install apidoc lint install_users install tests

