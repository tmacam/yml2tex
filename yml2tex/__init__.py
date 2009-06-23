#!/usr/bin/env python
# encoding: utf-8

"""
Transform a YAML file into a LaTeX Beamer presentation.

Copyright (C) 2009 Arthur Koziel <arthur@arthurkoziel.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__version__ = '1.2'
__author__ = 'Arthur Koziel <arthur@arthurkoziel.com>'
__url__ = 'http://code.google.com/p/yml2tex/'

import os
import optparse
import sys

import yaml
from loader import PairLoader

# TODO Beamer theme should be configurable


parser = optparse.OptionParser(
    usage="usage: %prog source_file [options]",
    version=__version__,
)

parser.add_option("-P", "--no-pause",
                  dest="list_pause", action="store_false", default=True,
                  help="Suppress emittion of pause/alert commands in lists.")
parser.add_option("-E", "--code-encoding",
                  dest="code_encoding", default="UTF-8", metavar="ENCODING",
                  help=("Sets the encoding used by include code. "
                        "Default is UTF-8."))

global_options = None # Overwrite w/ result from OptParse.parse_args()


def section(title):
    """
    Given the section title, return its corresponding LaTeX command.
    """
    return '\n\n\section{%s}' % _escape_output(title)

def subsection(title):
    """
    Given the subsection title, return its corresponding LaTeX command.
    """
    return '\n\subsection{%s}' % _escape_output(title)

def frame(title, items):
    """
    Given the frame title and corresponding items, delegate to the appropriate 
    function and returns its LaTeX commands.
    """
    if title.startswith('include'):
        out = code(title)
    elif title.startswith('image'):
        out = image(title, items)
    else:
        out = "\n\\begin{frame}[fragile,t]"
        out += "\n\t\\frametitle{%s}" % _escape_output(title)
        try:
            out += itemize(items)
        except TypeError:
            sys.stderr.write("ERR - ofending text %s %s\n" % (repr(title),
                            repr(items)))
            raise
        out += "\n\\end{frame}"
    return out

def _escape_output(text):
    """Escape special characters in Latex"""
    # FIXME Parse a character from input at a time and replace acordingly
    # see more at ftp://tug.ctan.org/pub/tex-archive/info/symbols/comprehensive/symbols-letter.pdf
    dic = {'&': '\&', 
           '$': '\$', 
           '%': '\%', 
           '#': '\#', 
           '_': '\_', 
           '{': '\{', 
           '}': '\}',
           '[': '\([\)',
           ']': '\(]\)',
           '<': r'\textless ',
           '>': r'\textgreater ',
           '|': r'\textbar~',
           '|': r'\textbar~',
           #'\\': r'\textbackslash~',
           '^': r'\^{}'} 
    # Escape letter that need to be escaped.
    # 
    # Since we process things a letter at a time we don't need to worry about
    # re-escaping reviously escaped characters --- as it would be the case have
    # we used replace.
    out = []
    for letter in text:
        # If letter doesn't need to be escaped, print letter as is
        out.append(dic.get(letter, letter))
    text = "".join(out)
    return text

def itemize(items):
    """
    Given the items for a frame, returns the LaTeX syntax for an itemized list.
    If an item itself is a list, a nested itemized list will be created.
    
    The script itself doesn't limit the depth of nested lists. LaTeX Beamer 
    limits lists to be nested up to a depth of 3.
    """
    out = "\n\t\\begin{itemize}"
    if global_options.list_pause:
        out += "[<+-| alert@+>]"
    for item in items:
        if isinstance(item, list):
            for i in item:
                out += "\n\t\\item %s" % _escape_output(item[0][0])
                out += itemize(item[0][1])
        else:
            if item.startswith('include'):
                out += inlinecode(item)
            else:
                out += "\n\t\\item %s" % _escape_output(item)
    out += "\n\t\end{itemize}"
    return out

def _output_code(filename):
    """Return code for filename in a LaTeX-ready format, possibly highlighted.

    If pygments is available, code will be highlighted. Otherwise we will
    use a plain lstlisting environment for the code.

    Args:
        filename: relative path of the file to be of code to be

    Returns:
        A Unicode string of the LaTeX version of the code to be included.
    
    Notice: 
        Enclosing Beamer frame should be marked as fragile.
    """
    # open the code file relative from the yml file path
    full_path = os.path.join(os.path.dirname(os.path.abspath(source_file)),
                             filename)
    f = open(full_path)
    # Code can be in another charset, convert it to unicode first
    code = f.read().decode(global_options.code_encoding)
    f.close()

    out = u""
    try:
        from pygments import highlight
        from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
        from pygments.formatters import LatexFormatter
        
        try:
            lexer = get_lexer_for_filename(filename)
        except:
            lexer = get_lexer_by_name('text')
        # For propper highlighting, we must handle unicode data to highlight()
        # This was performed at the start of this function, just proceed.
        out += "\n%s\n" % highlight(code, lexer, LatexFormatter(linenos=True))
    except ImportError:
        out += "\n\t\\begin{lstlisting}\n"
        out += code
        out += "\n\t\end{lstlisting}"
    # return code -- just make sure it is unicode
    return unicode(out)

def code(title):
    """
    Return syntax highlighted LaTeX.
    """
    filename = title.split(' ')[1]
    
    
    out = "\n\\begin{frame}[fragile,t]"
    out += "\n\t\\frametitle{Code: \"%s\"}" % filename
    out += _output_code(filename)
    out += "\n\end{frame}"
    return out

def inlinecode(title):
    """
    Return syntax highlighted LaTeX.
    """
    filename = title.split(' ')[1]
    
    out = "\n\\vspace{0.5em}"
    out += _output_code(filename)
    out += "\\vspace{0.5em}"
    return out

def image(title, options):
    """
    Given a frame title, which starts with "image" and is followed by the image 
    path, return the LaTeX command to include the image.
    """
    if not options:
        options = ""
    options = ",".join(["%s=%s" % (k, v) for k, v in dict(options).items()])
    
    out = "\n\\frame[shrink] {"
    out += "\n\t\\pgfimage[%s]{%s}" % (options, title.split(' ')[1])
    out += "\n}"
    return out

def header(metas):
    """
    Return the LaTeX Beamer document header declarations.
    """

    out = "\documentclass[slidestop,red]{beamer}"
    out += "\n\usepackage[utf8]{inputenc}"
    if metas.get('tex_babel'):
        out += "\n\usepackage[%s]{babel}" % metas['tex_babel']
    if metas.get('tex_fontenc'):
        out += "\n\usepackage[%s]{fontenc}" % metas['tex_fontenc']
    out += "\n\usepackage{fancyvrb,color}\n\n"
    
    # generate style definitions for pygments syntax highlighting
    try:
        from pygments.formatters import LatexFormatter
        out += LatexFormatter(style=metas.get('highlight_style', 'default')).get_style_defs()
    except ImportError:
        out += "\usepackage{listings}\n"
        out += "\lstset{numbers=left}"

    out += "\n\n\usetheme{Antibes}"
    out += "\n\setbeamertemplate{footline}[frame number]"
    out += "\n\usecolortheme{lily}"
    out += "\n\\beamertemplateshadingbackground{blue!5}{yellow!10}"
    
    if metas.has_key('short_title'):
        short_title = "[%s]" % metas.get('short_title')
    else:
        short_title = ""
    out += "\n\n\\title%s{%s}" % (short_title, metas.get('title', 'Example Presentation'))
    out += "\n\\author{%s}" % metas.get('author', 'Arthur Koziel')
    out += "\n\\institute{%s}" % metas.get('institute', '')
    out += "\n\date{%s}" % metas.get('date', '\\today')
    out += "\n\n\\begin{document}"
    out += "\n\n\\frame{\\titlepage}"
    
    if metas.get('outline', True):
        out += "\n\n\section*{%s}" % metas.get('outline_name', 'Outline')
        out += "\n\\frame {"
        out += "\n\t\\frametitle{%s}" % metas.get('outline_name', 'Outline')
        out += "\n\t\\tableofcontents"
        out += "\n}"

        out += "\n\n\AtBeginSection[] {"
        out += "\n\t\\frame{"
        out += "\n\t\t\\frametitle{%s}" % metas.get('outline_name', 'Outline')
        out += "\n\t\t\\tableofcontents[currentsection]"
        out += "\n\t}"
        out += "\n}"
    return out

def footer():
    """
    Return the LaTeX Beamer document footer.
    """
    out = "\n\end{document}"
    return out
    
def main():
    """
    Return the final LaTeX presentation after invoking all necessary functions.
    """
    global global_options
    global_options, args = parser.parse_args(sys.argv[1:])
    if not args:
        parser.print_help()
        sys.exit(1)
    try:
        global source_file
        source_file = args[0]
        doc = yaml.load(open(source_file), Loader=PairLoader)
    except IOError:
        parser.error("file does not exist")
        sys.exit(1)

    # yaml file is empty
    if not doc:
        sys.exit(1)
    
    metas = {}
    if doc[0][0] == 'metas':
        metas = dict(doc[0][1])
        del doc[0]

    out = header(metas)
    for sections, doc in doc:
        out += section(sections)
        for subsections, doc in doc:
            out += subsection(subsections)
            for frames, items in doc:
                out += frame(frames, items)
    out += footer()
    # LaTeX expects UTF-8 content
    return out.encode('utf-8')

if __name__ == '__main__':
    print main()
