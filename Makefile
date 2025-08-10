default: spec.pdf

spec.pdf: spec.tex _spec.tex
	lualatex spec.tex
	makeindex spec.idx
	lualatex spec.tex

_spec.tex: spec.zml compile.py
	python3 compile.py spec.zml

clean:
	rm -f spec.pdf
	rm -f _spec.tex
	rm -f _specmeta.tex
	rm -f _specannex.tex
	rm -f *.idx *.aux *.log *.ilg *.ind *.toc *.tmp *.ext *.xtr *.out
