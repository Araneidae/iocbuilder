# Makefile for building cothread documentation

# Ensure asciidoc is on the path.
PATH := $(PATH):/dls_sw/tools/local/bin

ASCIIDOC_FILES = $(wildcard *.txt)

HTML_FILES = $(patsubst %.txt, %.html, $(ASCIIDOC_FILES))

default: $(HTML_FILES) pydoc

clean:
	rm -f *.html *.xml
	rm -rf pydoc

%.html: %.txt
	asciidoc --attribute=quirks! --section-numbers -o $@ $<

pydoc: $(shell find ../iocbuilder -name \*.py)
	./makedocs.py
