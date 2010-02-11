NAME := vigiconf
PKGNAME := vigilo-$(NAME)
PYTHON := python
PREFIX := /usr
SYSCONFDIR := /etc
LOCALSTATEDIR := /var
CONFDIR := $(SYSCONFDIR)/vigilo/$(NAME)
VARDIR := $(LOCALSTATEDIR)/lib/vigilo/$(NAME)
DESTDIR = 

all: pkg/ssh_config pkg/$(PKGNAME).cron settings.ini build

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
	-useradd -s /bin/bash -M -d / -g $(NAME) -c 'Vigilo VigiConf user' $(NAME)
	if [ ! -f $(CONFDIR)/ssh/vigiconf.key ]; then \
	    ssh-keygen -t rsa -f $(CONFDIR)/ssh/vigiconf.key -N "" ;\
	fi
	chown $(NAME):$(NAME) $(CONFDIR)/ssh/vigiconf.key

install:
	python setup.py install --single-version-externally-managed --root=$(DESTDIR) --record=INSTALLED_FILES
	install -p -m 755 pkg/vigiconf.sh $(DESTDIR)$(PREFIX)/bin/vigiconf
	echo $(PREFIX)/bin/vigiconf >> INSTALLED_FILES
	chmod 750 $(DESTDIR)$(VARDIR)

install_permissions:
	chown -R $(NAME):$(NAME) $(DESTDIR)$(VARDIR)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(LOCALSTATEDIR)/lock/$(PKGNAME)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(CONFDIR)



include ../glue/Makefile.common
lint: lint_pylint
tests: tests_nose
clean: clean_python
	rm -f pkg/ssh_config pkg/$(PKGNAME).cron settings.ini


.PHONY: all clean install apidoc lint install_users install tests

