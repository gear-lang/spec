#!/usr/bin/env python3

from typing import List

import argparse
import os
import sys
import lxml
import lxml.etree

class AltSet:
    def __init__(self) -> None:
        self.strings: List[str] = []

class Rule:
    def __init__(self, term: str) -> None:
        self.term = term
        self.altsets: List[AltSet] = []
        self.columns = 0

def escape(text: str) -> str:
    latex_escapes = {
        '\\': r'\textbackslash{}',
        '{': r'\{',
        '}': r'\}',
        '#': r'\#',
        '$': r'\$',
        '%': r'\%',
        '&': r'\&',
        '_': r'\_',
        '^': r'\^{}',
        '~': r'\~{}',
        '“': r"``",
        '”': r"''",
    }
    return ''.join(latex_escapes.get(char, char) for char in text)

def process_paragraph(paragraph: str) -> str:
    paragraph = paragraph.strip()
    result = ""
    for line in paragraph.splitlines():
        result += line.strip()
        result += "\n"
    return result

def stringify(elem: lxml.etree._Element) -> str:
    string = ""
    if elem.text:
        string += elem.text
    for children in elem:
        if children.tail:
            string += children.tail
    return string

def stringify_escape(section_depth: int, elem: lxml.etree._Element) -> str:
    # Generate one giant text string of this element plus its children (recursively).
    string = ""
    if elem.text:
        string += escape(elem.text)
    for children in elem:
        string += visit(section_depth, children)
        if children.tail:
            string += escape(children.tail)
    return string

def visit(section_depth: int, elem: lxml.etree._Element) -> str:
    section = ""
    if elem.tag == "section":
        if section_depth == 0:
            section = "section"
        elif section_depth == 1:
            section = "subsection"
        elif section_depth == 2:
            section = "subsubsection"
        section_depth += 1

    # Wrap the text according to the relevent tag.
    if elem.tag == "html-only":
        return ""

    if elem.tag in ["chapter", "annex"]:
        out = "\\chapter{" + str(elem.attrib["title"]) + "}\n"
        id = elem.get("id")
        if id is not None:
            out += "\\label{" + id + "}\n"
        out += stringify_escape(section_depth, elem)
        return out

    if elem.tag == "section":
        out = "\\" + section + "{" + str(elem.attrib["title"]) + "}\n"
        id = elem.get("id")
        if id is not None:
            out += "\\label{" + id + "}\n"
        out += stringify_escape(section_depth, elem)
        return out

    if elem.tag == "index":
        string = stringify_escape(section_depth, elem)
        term = elem.get("term")
        if term is not None:
            out = "\\index{{{0}|(}}\n".format(term)
            out += string + "\n"
            out += "\\index{{{0}|)}}\n".format(term)
        else:
            out = "{0}\\index{{{0}}}\n".format(string)
        return out

    if elem.tag == "index-group":
        category = elem.get("category")
        term = elem.get("term")
        assert category is not None
        assert term is not None
        return "\\index{" + category + "!" + term + "}\n"

    if elem.tag == "lettrine":
        string = stringify_escape(section_depth, elem)
        return "\\lettrine[lraise=0, nindent=0em, slope=-.5em]{{{0}}}{{}}".format(string)
    
    if elem.tag == "code":
        out = "\\begin{lstlisting}\n"
        for line in stringify(elem).splitlines():
            if len(line.strip()) == 0:
                out += "@\\blankline@\n"
            else:
                out += line
                out += "\n"
        out += "\\end{lstlisting}\n"
        return out

    if elem.tag == "example":
        string = stringify_escape(section_depth, elem)
        out = "[\\textit{\\sffamily Example: }"
        out += process_paragraph(string)
        out += " \\textemdash~\\textit{\\sffamily end example}]"
        return out
    
    if elem.tag == "note":
        string = stringify_escape(section_depth, elem)
        out = "[\\textit{\\sffamily Note: }"
        out += process_paragraph(string)
        out += " \\textemdash~\\textit{\\sffamily end note}]"
        return out

    if elem.tag == "footnote":
        string = stringify_escape(section_depth, elem)
        desc = elem.get("desc")
        return f"{string}\\footnote{{{desc}}}"

    if elem.tag == "literal":
        string = stringify_escape(section_depth, elem)
        return "\\texttt{{{0}}}".format(string)

    if elem.tag == "para":
        string = stringify_escape(section_depth, elem)
        string = process_paragraph(string)
        return "\\par\n{0}\n".format(string)
    
    if elem.tag == "italic":
        string = stringify_escape(section_depth, elem)
        return "\\textit{{{0}}}".format(string)

    if elem.tag == "bold":
        string = stringify_escape(section_depth, elem)
        return "\\textbf{{{0}}}".format(string)

    if elem.tag == "br":
        return r"\\"

    # Do no break the line on any space characters.
    if elem.tag == "nobreak":
        string = stringify_escape(section_depth, elem)
        return string.replace(" ", "~")

    if elem.tag == "table":
        # id = elem.get("id")
        # caption = elem.get("caption")
        alignment = elem.get("alignment")
        assert alignment is not None
        style = elem.get("style")
        out = "\\begin{center}\n"
        # out += "\\begin{table}[hbt!]\n"
        # if caption is not None and id is not None:
        #     out += "\\caption{" + caption + "}"
        #     out += "\\label{" + id + "}\n"
        out += "\\begin{tabular}{|"
        for index,align in enumerate(alignment):
            out += f"{align}"
            if index < len(alignment) - 1:
                if style != "list":
                    out += "|" # line between columns
        out += "|}\n"
        out += "\\hline\n" # top line
        for row_index,row in enumerate(elem):
            assert row.tag == "row"
            assert len(alignment) == len(row)
            makecell = "thead" if row.get("head") is not None else "makecell"
            for index,cell in enumerate(row):
                assert cell.tag == "cell"
                out += f"\\{makecell}[t]{{" + stringify_escape(section_depth, cell) + "}"
                if index < len(row) - 1:
                    out += "&"
                else:
                    out += r"\\"
            out += "\n"
            if row_index < len(elem) - 1:
                if style != "list":
                    out += "\\hline\n" # line between rows
        out += "\\hline\n" # bottom line
        out += "\\end{tabular}\n"
        # out += "\\end{table}\n"
        out += "\\end{center}\n"
        return out

    if elem.tag in ["tip", "note"]:
        out = f"\\Admonition[{elem.tag}]{{\n"
        out += f"\\AdmonitionTitle{{{elem.tag.title()}}}\n"
        out += "\n"
        out += stringify_escape(section_depth, elem)
        out += "}\n"
        return out

    if elem.tag in ["ul", "ol"]:
        tag = "enumerate" if elem.tag == "ol" else "itemize"
        out = f"\\begin{{{tag}}}\n"
        for children in elem:
            assert children.tag == "li"
            out += "\\item{" + stringify_escape(section_depth, children) + "}\n"
        out += f"\\end{{{tag}}}\n"
        return out

    if elem.tag == "grammar":
        # The grammar needs a production term otherwise what is it defining?
        term = elem.get("term")
        if term is None:
            print("missing <term> attribute")
            return "?"
        # Some grammar blocks should not be indexed either in the annex AND should not be linkable.
        noref = elem.get("example") is not None
        # Convert alts and altsets into a common format.
        oneof = False
        rule = Rule(term)
        for children in elem:
            altset = AltSet()
            if children.tag == "alt":
                altset.strings.append(stringify_escape(section_depth, children))
                rule.columns = max(rule.columns, 1)
            elif children.tag == "altset":
                oneof = True
                for child in children:
                    altset.strings.append(stringify_escape(section_depth, child))
                rule.columns = max(rule.columns, len(children))
            else:
                print("unknown grammar tag:", elem.tag)
            rule.altsets.append(altset)
        # Serialize the BNF rules.
        if noref:
            out = "\\begin{bnfnoindex}"
        else:
            out = "\\begin{bnf}"
        out += "[term=" + rule.term
        if oneof:
            out += ",oneof=true"
        out += "]{"
        for _ in range(rule.columns):
            out += "l"
        out += "}\n"
        for altset in rule.altsets:
            # Each column of a production rule.
            for column in range(rule.columns):
                if column >= len(altset.strings):
                    out += " & "
                    continue
                if column > 0 and column < len(altset.strings):
                    out += " & "
                out += altset.strings[column].replace(" ", "~~~")
            out += r" \\"
            out += "\n"
        if noref:
            out += "\\end{bnfnoindex}\n"
        else:
            out += "\\end{bnf}\n"
        return out

    if elem.tag == "informative":
        out = "\\par\n"
        out += "\\textbf{This clause is informative.}\n"
        out += "\\par\n"
        out += stringify_escape(section_depth, elem)
        out += "\\par\n"
        out += "\\textbf{End of informative text.}\n"
        out += "\\par\n"
        return out

    if elem.tag == "ref":
        id = elem.get("id")
        if id is None:
            print("missing <id> attribute")
            return "?"
        string = stringify_escape(section_depth, elem)
        if len(string.strip()) == 0:
            return "\\ref{" + id + "}"
        return string + "~\\ref{" + id + "}"

    # This reference is specifically for linking to sections and not tables or listings.
    # This is because in the latex it prefixes the referende with the "§" character
    # which indicates a chapter or section.
    if elem.tag == "partref":
        id = elem.get("id")
        if id is None:
            print("missing <id> attribute")
            return "?"
        string = stringify_escape(section_depth, elem)
        if len(string.strip()) == 0:
            return "\\partref{" + id + "}"
        return string + "~\\partref{" + id + "}"

    if elem.tag == "quoted":
        string = stringify(elem)
        string = string.replace("\\", "\\textbackslash???")
        string = string.replace("{", "\\{")
        string = string.replace("}", "\\}")
        string = string.replace("&", "\\&")
        string = string.replace("#", "\\#")
        string = string.replace("~", "\\textasciitilde{}")
        string = string.replace("^", "\\textasciicircum{}")
        string = string.replace("\\textbackslash???", "\\textbackslash{}")  # This is a hack to add the curly braces back after escaping them.
        return "\\nonterminal{" + string + "}"

    if elem.tag == "alt":
        return stringify_escape(section_depth, elem)

    if elem.tag == "term":
        string = stringify_escape(section_depth, elem)
        return "\\terminal{" + string + "}"

    if elem.tag == "opt-term":
        string = stringify_escape(section_depth, elem)
        return "\\optterminal{" + string + "}"
    
    if elem.tag == "grammarterm":
        string = stringify_escape(section_depth, elem)
        return "\\hyperref[grammar:" + string + "]{\\grammarterm{" + string + "}}"

    if elem.tag == "latexmath":
        if elem.text is None:
            elem.text = ""
        return "\\(" + elem.text + "\\)"

    if elem.tag == "latexbigmath":
        if elem.text is None:
            elem.text = ""
        out = "\\[\n"
        out += elem.text.strip()
        out += "\n"
        out += "\\]\n"
        return out
    
    if elem.tag == "sub":
        if elem.text is None:
            elem.text = ""
        return "\\(_{" + elem.text + "}\\)"

    print("unknown tag:", elem.tag)
    return stringify_escape(section_depth, elem)

class Arguments(argparse.Namespace):
    def __init__(self) -> None:
        self.infile = ""

def parse_args() -> int:
    parser = argparse.ArgumentParser(prog="process", description="Process XML into LaTeX.")
    parser.add_argument("infile")

    args = Arguments()
    args = parser.parse_args(namespace=args)

    root = lxml.etree.parse(args.infile)
    root.xinclude()
    outfile, _ = os.path.splitext(os.path.basename(args.infile))

    with open(f"_{outfile}.tex", "w", encoding="utf-8") as out:
        for child in root.xpath("//chapters/chapter"):
            if isinstance(child, lxml.etree._Element):
                out.write(visit(0, child))

    with open(f"_{outfile}annex.tex", "w", encoding="utf-8") as out:
        for child in root.xpath("//annexes/annex"):
            if isinstance(child, lxml.etree._Element):
                out.write(visit(0, child))

    with open(f"_{outfile}meta.tex", "w", encoding="utf-8") as out:
        for title in root.xpath("//title"):
            out.write("\\title{" + title.text + "}\n")

    return 0

if __name__ == "__main__":
    sys.exit(parse_args())
