JAVA_HOME ?= /usr
export JAVA_HOME

A2X := a2x --icons
ASCIIDOC := asciidoc -a icons -a toc

INPUTS := searching.txt indexing.txt

default:  html pdf
html: $(patsubst %.txt, %.html, $(INPUTS))
pdf: $(patsubst %.txt, %.pdf, $(INPUTS))

%.pdf: %.txt images/icons
	$(A2X) -f pdf $<

%.html: %.txt images/icons
	$(ASCIIDOC) -o $@ $<

clean:
	rm *.html *.pdf *.fo *.xml

images/icons:
	@[ -d images ] || mkdir images
	if [ -d /usr/share/asciidoc/icons ]; then \
		ln -s /usr/share/asciidoc/icons images/icons; \
	elif [ -d /etc/asciidoc/images/icons ]; then \
		ln -s /etc/asciidoc/images/icons images/icons; \
	else \
		echo "*** asciidoc images could not be found"; \
	fi

.PHONY: html pdf default clean
# vim:ts=8:sts=8:noet
