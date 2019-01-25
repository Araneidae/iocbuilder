# Specify defaults for testing
PREFIX := $(shell pwd)/prefix
PYTHON = dls-python
INSTALL_DIR = $(PREFIX)/lib/python2.7/site-packages
SCRIPT_DIR = $(PREFIX)/bin
MODULEVER=0.0

# Override with any release info
-include Makefile.private

# This is run when we type make
dist: setup.py $(wildcard iocbuilder/*) $(wildcard xmlbuilder/*) make_docs
	MODULEVER=$(MODULEVER) $(PYTHON) setup.py bdist_egg
	touch dist

# Clean the module
clean:
	$(PYTHON) setup.py clean
	-rm -rf build dist *egg-info installed.files
	-find -name '*.pyc' -exec rm {} \;
	$(MAKE) -C documentation clean

# Install the built egg
install: dist
	mkdir -p $(INSTALL_DIR)
	$(PYTHON) setup.py easy_install -m \
            --record=installed.files \
            --install-dir=$(INSTALL_DIR) \
            --script-dir=$(SCRIPT_DIR) dist/*.egg
	ln -fs $(shell pwd)/toolkit/merge-iocs $(SCRIPT_DIR)/dls-merge-iocs        

make_docs:
	$(MAKE) -C documentation
