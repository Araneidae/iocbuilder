export EPICS_BASE = /dls_sw/epics/R3.14.11/base

KEEP_FILES = Makefile etc README

install: Makefile.builder
	make -f Makefile.builder

clean:
	rm -rf $(filter-out $(KEEP_FILES),$(wildcard *))

Makefile.builder: $(wildcard etc/*)
	python etc/makeioc.py
