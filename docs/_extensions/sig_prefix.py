from __future__ import annotations

import re

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.domains.python import PyFunction, PyMethod
from sphinx.ext.autodoc import FunctionDocumenter, MethodDocumenter
from sphinx.writers.html5 import HTML5Translator


NAME_RE: re.Pattern[str] = re.compile(r"(?P<module>[\w.]+\.)?(?P<method>\w+)")
PYTHON_DOC_STD: str = "https://docs.python.org/3/library/stdtypes.html"


class hrnode(nodes.General, nodes.Element):
    pass


class usagetable(nodes.General, nodes.Element):
    pass


class aiter(nodes.General, nodes.Element):
    pass


def visit_usagetable_node(self: HTML5Translator, node: usagetable):
    self.body.append(self.starttag(node, "div", CLASS="sig-usagetable"))


def depart_usagetable_node(self: HTML5Translator, node: usagetable):
    self.body.append("</div>")


def visit_aiterinfo_node(self: HTML5Translator, node: aiter):
    dot = "." if node.get("python-class-name", False) else ""

    self.body.append(self.starttag(node, "span", CLASS="pre"))

    self.body.append("<em>await </em>")
    self.body.append(self.starttag(node, "span", CLASS="sig-name"))
    self.body.append(f"{dot}{node['python-name']}(...)</span>")

    self.body.append(self.starttag(node, "span"))
    self.body.append(" -> ")
    self.body.append("</span>")

    list_ = f"{PYTHON_DOC_STD}#list"
    self.body.append(self.starttag(node, "a", href=list_))
    self.body.append("list")
    self.body.append("</a>")

    self.body.append("[T]")

    self.body.append(self.starttag(node, "br"))

    self.body.append("<em>async for</em> item in ")
    self.body.append(self.starttag(node, "span", CLASS="sig-name"))
    self.body.append(f"{dot}{node['python-name']}(...)")
    self.body.append("</span>")
    self.body.append(":")


def depart_aiterinfo_node(self: HTML5Translator, node: aiter):
    self.body.append("</span>")


def visit_hr_node(self: HTML5Translator, node: hrnode):
    self.body.append(self.starttag(node, "hr"))


def depart_hr_node(self: HTML5Translator, node: hrnode):
    self.body.append("</hr>")


def check_return(sig: str) -> bool:
    if not sig:
        return False

    splat = sig.split("->")
    ret = splat[-1]

    return "HTTPAsyncIterator" in ret


class AiterPyF(PyFunction):
    option_spec = PyFunction.option_spec.copy()
    option_spec.update({"aiter": directives.flag, "deco": directives.flag})

    def parse_name_(self, content: str) -> tuple[str | None, str]:
        match = NAME_RE.match(content)

        if match is None:
            raise RuntimeError(f"content {content} somehow doesn't match regex in {self.env.docname}.")

        path, name = match.groups()

        if path:
            modulename = path.rstrip(".")
        else:
            modulename = self.env.temp_data.get("autodoc:module")
            if not modulename:
                modulename = self.env.ref_context.get("py:module")

        return modulename, name

    def get_signature_prefix(self, sig: str) -> list[nodes.Node]:
        mname, name = self.parse_name_(sig)

        if "aiter" in self.options:
            node = aiter()
            node["python-fullname"] = f"{mname}.{name}"
            node["python-name"] = name
            node["python-module"] = mname

            parent = usagetable("", node)
            return [parent, hrnode(), addnodes.desc_sig_keyword("", "async"), addnodes.desc_sig_space()]
        elif "deco" in self.options:
            return [addnodes.desc_sig_keyword("", "@"), addnodes.desc_sig_space()]

        return super().get_signature_prefix(sig)


class AiterPyM(PyMethod):
    option_spec = PyMethod.option_spec.copy()
    option_spec.update({"aiter": directives.flag, "deco": directives.flag})

    def parse_name_(self, content: str) -> tuple[str, str]:
        match = NAME_RE.match(content)

        if match is None:
            raise RuntimeError(f"content {content} somehow doesn't match regex in {self.env.docname}.")

        cls, name = match.groups()
        return cls, name

    def get_signature_prefix(self, sig: str) -> list[nodes.Node]:
        cname, name = self.parse_name_(sig)

        if "aiter" in self.options:
            node = aiter()
            node["python-name"] = name
            node["python-class-name"] = cname

            parent = usagetable("", node)
            return [parent, hrnode(), addnodes.desc_sig_keyword("", "async"), addnodes.desc_sig_space()]
        elif "deco" in self.options:
            return [addnodes.desc_sig_keyword("", "@"), addnodes.desc_sig_space()]

        return super().get_signature_prefix(sig)


class AiterFuncDocumenter(FunctionDocumenter):
    objtype = "function"
    priority = FunctionDocumenter.priority + 1

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()
        docs = self.object.__doc__ or ""

        if docs.startswith("|aiter|") or check_return(sig):
            self.add_line("   :aiter:", sourcename)
        elif docs.startswith("|deco|"):
            self.add_line("   :deco:", sourcename)


class AiterMethDocumenter(MethodDocumenter):
    objtype = "method"
    priority = MethodDocumenter.priority + 1

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()
        obj = self.parent.__dict__.get(self.object_name, self.object)

        docs = obj.__doc__ or ""
        if docs.startswith("|aiter|") or check_return(sig):
            self.add_line("   :aiter:", sourcename)
        elif docs.startswith("|deco|"):
            self.add_line("   :deco:", sourcename)


def setup(app: Sphinx) -> dict[str, bool]:
    app.setup_extension("sphinx.directives")
    app.setup_extension("sphinx.ext.autodoc")

    app.add_directive_to_domain("py", "function", AiterPyF, override=True)
    app.add_directive_to_domain("py", "method", AiterPyM, override=True)

    app.add_autodocumenter(AiterMethDocumenter, override=True)
    app.add_autodocumenter(AiterFuncDocumenter, override=True)

    app.add_node(aiter, html=(visit_aiterinfo_node, depart_aiterinfo_node))
    app.add_node(usagetable, html=(visit_usagetable_node, depart_usagetable_node))
    app.add_node(hrnode, html=(visit_hr_node, depart_hr_node))

    return {"parallel_read_safe": True}
