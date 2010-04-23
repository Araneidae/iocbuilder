export EPICS_BASE = /dls_sw/epics/R3.14.11/base

install: Makefile.builder
	make -f Makefile.builder

clean:
	rm -rf $(filter-out etc Makefile,$(wildcard *))

Makefile.builder: $(wildcard etc/*)
	python etc/makeioc.py
