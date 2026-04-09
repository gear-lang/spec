XML_FILES := $(wildcard *.xml)

default: spec.pdf

spec.pdf: spec.tex _spec.tex
	lualatex spec.tex
	makeindex spec.idx
	lualatex spec.tex

_spec.tex: compile.py $(XML_FILES)
	python3 compile.py spec.xml

clean:
	rm -f spec.pdf
	rm -f _spec.tex
	rm -f _specmeta.tex
	rm -f _specannex.tex
	rm -f *.idx *.aux *.log *.ilg *.ind *.toc *.tmp *.ext *.xtr *.out
