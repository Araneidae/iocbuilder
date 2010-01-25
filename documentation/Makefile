# this is the doxygen output dir
DOCDIR := doxygen

# add the documentation files to the install target
all install: $(DOCDIR)

# rule for documentation
$(DOCDIR): config.src manual.src
	mkdir -p $(DOCDIR)
	cd $(DOCDIR); /dls_sw/work/common/python/documentation/src/documentation.py config.src manual.src

# Remove entire documentation/doxygen dir on clean
clean:
	rm -rf $(DOCDIR)
