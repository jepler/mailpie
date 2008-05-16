default: searching.html searching.pdf

%.pdf: %.txt
	a2x --icons -f pdf $<

%.html: %.txt
	asciidoc -a icons -a toc -o $@ $<

# vim:ts=8:sts=8:noet
