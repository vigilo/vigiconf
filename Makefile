NAME = confmgr
CONFDIR = /etc/$(NAME)
BINDIR = /usr/bin
SBINDIR = /usr/sbin
DATADIR = /usr/share/vigilo-$(NAME)
LOCALSTATEDIR = /var/lib/vigilo-$(NAME)
LOCKDIR = /var/lock/vigilo-$(NAME)
DESTDIR = 

all:
	@echo "Targets: install, clean, tarball, apidoc, lint"

install_users:
	@echo "Creating the $(NAME) user..."
	-groupadd $(NAME)
	-useradd -s /bin/bash -m -d /home/$(NAME) -g $(NAME) -c 'VigiConf user' $(NAME)

install:
	## Application
	-mkdir -p $(DESTDIR)$(DATADIR)
	for file in src/*.py; do \
		install -p -m 644 $$file $(DESTDIR)$(DATADIR)/`basename $$file` ;\
	done
	chmod +x $(DESTDIR)$(DATADIR)/{dispatchator.py,debug.py,discoverator.py}
	for dir in lib generators tests validation; do \
		cp -pr src/$$dir $(DESTDIR)$(DATADIR)/ ;\
	done
	## Configuration
	-mkdir -p $(DESTDIR)$(CONFDIR)/{conf.d,new,prod}
	# Don't overwrite
	[ -f $(DESTDIR)$(CONFDIR)/$(NAME).conf ] || \
		install -p -m 640 src/$(NAME).conf $(DESTDIR)$(CONFDIR)/$(NAME).conf
	# Overwrite this one, it's our examples
	-[ -d $(DESTDIR)$(CONFDIR)/conf.d.example ] && \
		rm -rf $(DESTDIR)$(CONFDIR)/conf.d.example
	cp -pr src/conf.d $(DESTDIR)$(CONFDIR)/conf.d.example
	mv -f $(DESTDIR)$(CONFDIR)/conf.d.example/README.source $(DESTDIR)$(CONFDIR)/conf.d/
	## Cleanup
	find $(DESTDIR)$(CONFDIR)/conf.d.example $(DESTDIR)$(DATADIR) -type d -name .svn -print | xargs rm -rf
	## Var data
	-mkdir -p $(DESTDIR)$(LOCALSTATEDIR)/{db,deploy,revisions}
	-mkdir -p $(DESTDIR)/var/lock/vigilo-$(NAME)
	# Don't overwrite
	[ -f $(DESTDIR)$(LOCALSTATEDIR)/db/ssh_config ] || \
		install -p -m 644 pkg/ssh_config $(DESTDIR)$(LOCALSTATEDIR)/db/ssh_config
	chmod 750 $(DESTDIR)$(LOCALSTATEDIR)
	-mkdir -p $(DESTDIR)$(LOCKDIR)
	## Launchers
	-mkdir -p $(DESTDIR)$(BINDIR)
	sed -e 's,@DATADIR@,$(DATADIR),g' pkg/$(NAME).sh > $(DESTDIR)$(BINDIR)/$(NAME)
	chmod 755 $(DESTDIR)$(BINDIR)/$(NAME)
	touch --reference pkg/$(NAME).sh $(DESTDIR)$(BINDIR)/$(NAME)
	sed -e 's,@DATADIR@,$(DATADIR),g' pkg/discoverator.sh > $(DESTDIR)$(BINDIR)/discoverator
	chmod 755 $(DESTDIR)$(BINDIR)/discoverator
	touch --reference pkg/discoverator.sh $(DESTDIR)$(BINDIR)/discoverator
	-mkdir -p $(DESTDIR)$(SBINDIR)
	install -p -m 755 pkg/dispatchator.sh $(DESTDIR)$(SBINDIR)/dispatchator
	## Cron job (don't overwrite)
	-mkdir -p $(DESTDIR)/etc/cron.d/
	[ -f $(DESTDIR)/etc/cron.d/$(NAME) ] || \
		install -p -m 644 pkg/cronjobs $(DESTDIR)/etc/cron.d/$(NAME)
	## information about the sudo setup for the user

install_permissions:
	chown -R $(NAME):$(NAME) $(DESTDIR)$(LOCALSTATEDIR)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(LOCKDIR)
	chown -R $(NAME):$(NAME) $(DESTDIR)$(CONFDIR)

clean:
	find $(CURDIR) -name "*.pyc" -exec rm {} \;
	find $(CURDIR) -name "*~" -exec rm {} \;

apidoc: doc/apidoc/index.html
doc/apidoc/index.html: $(wildcard src/*.py) src/lib src/generators
	rm -rf $(CURDIR)/doc/apidoc
	PYTHONPATH=src VIGICONF_MAINCONF="$(CURDIR)/src/$(NAME)-test.conf" \
		epydoc -o $(dir $@) -v --name Vigilo --url http://www.projet-vigilo.org \
		--docformat=epytext $^

lint: $(wildcard src/*.py) src/lib src/generators
	PYTHONPATH=src pylint $^

tests:
	VIGICONF_MAINCONF=src/confmgr-test.conf nosetests unittests

.PHONY: all tarball clean install apidoc lint install_users install install_permissions tests

