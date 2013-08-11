#!/usr/bin/env make -f

PREFIX ?= /usr/local

LOCALESDIR ?= /share/locale

all:

include Makefile.general

mo-generate:
	@(cd po/ && env LOCALESDIR=$(DESTDIR)$(PREFIX)$(LOCALESDIR) $(MAKE) generate)


install: install-core install-data install-utils
	install -m 644 $(ALLMODS) $(DESTDIR)$(PREFIX)/share/games/pydance
	install -m 755 pydance.py $(DESTDIR)$(PREFIX)/share/games/pydance
	ln -sf ../share/games/pydance/pydance.py $(DESTDIR)$(PREFIX)/games/pydance
	@(cd po/ && env LOCALESDIR=$(DESTDIR)$(PREFIX)$(LOCALESDIR) $(MAKE) $@)

install-core:
	install -d $(DESTDIR)$(PREFIX)/bin $(DESTDIR)$(PREFIX)/games $(DESTDIR)$(PREFIX)/share/games/pydance
	install -d $(DESTDIR)$(PREFIX)/share/games/pydance/songs
	install -d $(DESTDIR)$(PREFIX)/share/man/man1 $(DESTDIR)$(PREFIX)/share/man/man6

install-utils: install-core
	for U in $(UTILS); do\
	  install -m 755 $$U `echo $(DESTDIR)$(PREFIX)/bin/$$U | sed 's/\.py//' | sed 's/utils\///'`;\
	done

install-data: install-core
	cp -R $(DATA) $(DESTDIR)$(PREFIX)/share/games/pydance
	cp docs/man/*.1 $(DESTDIR)$(PREFIX)/share/man/man1
	cp docs/man/*.6 $(DESTDIR)$(PREFIX)/share/man/man6
	cp pydance.posix.cfg pydance.cfg
	install -D -m 644 pydance.cfg $(DESTDIR)$(PREFIX)/etc/pydance.cfg

install-zip: pydance.zip install-core install-data install-utils
	install -m 644 constants.py pydance.zip $(DESTDIR)$(PREFIX)/share/games/pydance
	install -m 755 pydance.py $(DESTDIR)$(PREFIX)/share/games/pydance
	ln -sf ../share/games/pydance/pydance.py $(DESTDIR)$(PREFIX)/games/pydance
