"""HTML snapshot parser helpers."""

from .common import HtmlAnchorSnapshot, HtmlDocumentSnapshot, _SnapshotHTMLParser

def parse_html_snapshot(html: str) -> HtmlDocumentSnapshot:
    parser = _SnapshotHTMLParser()
    parser.feed(str(html or ""))
    parser.close()
    return HtmlDocumentSnapshot(anchors=parser.anchors, ld_json_scripts=parser.ld_json_scripts)
