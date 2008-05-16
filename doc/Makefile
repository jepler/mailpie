JAVA_HOME ?= /usr
export JAVA_HOME

INPUTS := searching.txt indexing.txt

default:  html pdf
html: $(patsubst %.txt, %.html, $(INPUTS))
pdf: $(patsubst %.txt, %.pdf, $(INPUTS))

%.pdf: %.txt
	a2x --icons -f pdf $<

%.html: %.txt
	asciidoc -a icons -a toc -o $@ $<

clean:
	rm *.html *.pdf *.fo *.xml
.PHONY: html pdf default clean
# vim:ts=8:sts=8:noet
