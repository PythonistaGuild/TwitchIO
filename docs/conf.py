# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


import os

# -- Project information -----------------------------------------------------
import re
import sys


sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath(".."))
sys.path.append(os.path.abspath("_extensions"))

on_rtd = os.environ.get("READTHEDOCS") == "True"
project = "TwitchIO"
copyright = "2017-Current, PythonistaGuild"
author = "PythonistaGuild"

# The full version, including alpha/beta/rc tags
release = ""
with open("../twitchio/__init__.py") as f:
    release = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)  # type: ignore

version = release
# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "details",
    "attributetable",
    "hoverxref.extension",
    "sphinxcontrib_trio",
    "sphinx_wagtail_theme",
    "sig_prefix",
    "exc_hierarchy",
]

# Add any paths that contain templates here, relative to this directory.
# templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_wagtail_theme"
html_last_updated_fmt = "%b %d, %Y"
# html_logo = "logo.png"

html_theme_options = dict(
    project_name="Documentation",
    github_url="https://github.com/PythonistaGuild/TwitchIO/tree/main/docs/",
    logo="logo.png",
    logo_alt="TwitchIO",
    logo_height=120,
    logo_url="/",
    logo_width=120,
    footer_links=",".join(
        [
            "GitHub|https://github.com/PythonistaGuild/TwitchIO",
            "Discord|https://discord.gg/RAKc3HF",
            "Documentation|https://twitchio.dev",
        ]
    ),
    header_links="Examples|https://github.com/PythonistaGuild/TwitchIO/tree/main/examples",
)

copyright = "2017 - Present, PythonistaGuild"
html_show_copyright = True
html_show_sphinx = False

html_last_updated_fmt = "%b %d, %Y - %H:%M:%S"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.styles" will overwrite the builtin "default.styles".
# These folders are copied to the documentation's HTML output
html_static_path = ["_static"]

# These paths are either relative to html_static_path
# or fully qualified paths (eg. https://...)
html_css_files = ["custom.css", "codeblocks.css"]
html_js_files = ["custom.js"]

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
autodoc_member_order = "bysource"

rst_prolog = """
.. |coro| replace:: This function is a |corourl|_.
.. |maybecoro| replace:: This function *could be a* |corourl|_.
.. |corourl| replace:: *coroutine*
.. _corourl: https://docs.python.org/3/library/asyncio-task.html#coroutine
.. |deco| replace:: This function is a **decorator**.
.. |aiter| replace:: **This function returns a** :class:`~twitchio.HTTPAsyncIterator`
.. |token_for| replace:: An optional User-ID, or PartialUser object, that will be used to find an appropriate managed user token for this request. See: :meth:`~twitchio.Client.add_token` to add managed tokens to the client.
.. |extmodule| replace:: ...
"""

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

intersphinx_mapping = {
    "py": ("https://docs.python.org/3", None),
}

extlinks = {
    "tioissue": ("https://github.com/PythonistaGuild/Twitchio/issues/%s", "GH-%s"),
    "es-docs": ("https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/#%s", "Twitch Eventsub %s"),
}


# Hoverxref Settings...
hoverxref_auto_ref = True
hoverxref_intersphinx = ["py"]

hoverxref_role_types = {
    "hoverxref": "modal",
    "ref": "modal",
    "confval": "tooltip",
    "mod": "tooltip",
    "class": "tooltip",
    "attr": "tooltip",
    "func": "tooltip",
    "meth": "tooltip",
    "exc": "tooltip",
}

hoverxref_roles = list(hoverxref_role_types.keys())
hoverxref_domains = ["py"]
hoverxref_default_type = "tooltip"
hoverxref_tooltip_theme = ["tooltipster-punk", "tooltipster-shadow", "tooltipster-shadow-custom"]


pygments_style = "sphinx"
pygments_dark_style = "monokai"


html_experimental_html5_writer = True


def autodoc_skip_member(app, what, name, obj, skip, options):
    exclusions = ("__weakref__", "__doc__", "__module__", "__dict__", "__init__")
    exclude = name in exclusions

    return True if exclude else None


def setup(app):
    app.connect("autodoc-skip-member", autodoc_skip_member)
