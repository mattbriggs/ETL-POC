"""Pure DITA XML construction functions (functional core).

All functions are pure: given the same inputs they always return the same
output and have no side effects. They produce well-formed DITA 1.3 XML
fragments as plain strings; serialisation to disk is handled by the
imperative shell.
"""

from __future__ import annotations

import pathlib
import re
import xml.sax.saxutils as saxutils


# ---------------------------------------------------------------------------
# DocBook → DITA extraction helpers (pure string operations)
# ---------------------------------------------------------------------------


def extract_title(docbook_text: str) -> str:
    """Extract the first ``<title>`` value from DocBook XML text.

    :param docbook_text: Raw DocBook XML string.
    :returns: Title text, or ``"Untitled"`` if no ``<title>`` element is found.
    """
    match = re.search(r"<title>(.*?)</title>", docbook_text, re.IGNORECASE)
    return match.group(1) if match else "Untitled"


def extract_body(docbook_text: str) -> str:
    """Extract paragraph content from DocBook XML text as DITA ``<p>`` elements.

    Paragraphs inside ``<para>`` elements are converted; if none are found
    the plain text is wrapped in a single ``<p>``.

    :param docbook_text: Raw DocBook XML string.
    :returns: String of one or more ``<p>`` elements suitable for embedding
        in a DITA topic body.
    """
    paras = re.findall(r"<para>(.*?)</para>", docbook_text, re.IGNORECASE | re.DOTALL)
    if paras:
        return "".join(f"<p>{p.strip()}</p>" for p in paras)
    # Fallback: strip all tags and wrap in a single paragraph.
    plain = re.sub(r"<[^>]+>", "", docbook_text)[:200]
    return f"<p>{saxutils.escape(plain)}</p>"


# ---------------------------------------------------------------------------
# DITA topic builders (pure)
# ---------------------------------------------------------------------------

_TOPIC_BUILDERS: dict[str, str] = {
    "concept": '<concept id="{id}"><title>{title}</title><conbody>{body}</conbody></concept>',
    "task": '<task id="{id}"><title>{title}</title><taskbody>{body}</taskbody></task>',
    "reference": (
        '<reference id="{id}"><title>{title}</title><refbody>{body}</refbody></reference>'
    ),
}


def build_topic(title: str, body: str, topic_type: str, topic_id: str = "t1") -> str:
    """Render a minimal DITA 1.3 topic element.

    :param title: Topic title text (will be XML-escaped).
    :param body: Pre-formatted body content (inserted verbatim — caller is
        responsible for validity).
    :param topic_type: One of ``"concept"``, ``"task"``, or ``"reference"``.
    :param topic_id: Value for the element's ``id`` attribute.
    :returns: Serialised DITA topic XML string.
    :raises ValueError: If *topic_type* is not a known type.

    :Example:

    .. code-block:: python

        xml = build_topic("Installation", "<p>Run the installer.</p>", "task")
    """
    template = _TOPIC_BUILDERS.get(topic_type)
    if template is None:
        raise ValueError(
            f"Unknown topic_type '{topic_type}'. Expected one of: "
            + ", ".join(sorted(_TOPIC_BUILDERS))
        )
    return template.format(
        id=topic_id,
        title=saxutils.escape(title),
        body=body,
    )


# ---------------------------------------------------------------------------
# DITA map builder (pure)
# ---------------------------------------------------------------------------

_MAP_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">
<map>
  <title>{title}</title>
{refs}
</map>
"""


def make_topicref(topic_path: str, base_dir: str) -> str:
    """Build a ``<topicref>`` element with a path relative to the map file.

    :param topic_path: Absolute or relative path to the DITA topic file.
    :param base_dir: Directory that the DITA map will be written to. The
        ``href`` attribute will be relative to this directory.
    :returns: A ``<topicref href="..." />`` XML string.
    """
    abs_path = pathlib.Path(topic_path).resolve()
    rel_path = abs_path.relative_to(pathlib.Path(base_dir).resolve(), walk_up=True)
    return f'  <topicref href="{rel_path.as_posix()}" />'


def build_map(title: str, topic_paths: list[str], base_dir: str) -> str:
    """Build a complete DITA map XML document.

    :param title: Human-readable map title (will be XML-escaped).
    :param topic_paths: Paths to all DITA topic files to include, in order.
    :param base_dir: Directory where the map will be written (used to compute
        relative ``href`` values).
    :returns: Complete DITA map XML as a string.
    """
    refs = "\n".join(make_topicref(p, base_dir) for p in sorted(topic_paths))
    return _MAP_TEMPLATE.format(
        title=saxutils.escape(title),
        refs=refs,
    )
