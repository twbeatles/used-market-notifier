"""Compatibility facade for marketplace parser helpers."""

from .html_snapshot import HtmlAnchorSnapshot, HtmlDocumentSnapshot, parse_html_snapshot
from .normalization import (
    is_count_or_metric_line,
    is_malformed_listing_title,
    is_strict_price_line,
    looks_like_time_line,
    normalize_location_value,
    normalize_multiline_text,
    normalize_price_text,
    normalize_whitespace,
)
from .metadata import (
    extract_label_value,
    extract_location_from_text,
    extract_profile_name_from_aria_label,
    merge_item_metadata,
    normalize_sale_status,
    pick_seller_candidate,
)
from .urls import extract_bunjang_product_id, extract_numeric_article_id, normalize_url_for_match, validate_platform_url
from .bunjang import BunjangCardParseResult, parse_bunjang_card_text, parse_bunjang_detail_payload, parse_bunjang_search_items
from .quality import evaluate_scrape_quality
from .joonggonara import (
    classify_joonggonara_candidate,
    is_valid_joonggonara_title,
    parse_joonggonara_detail_text,
    parse_joonggonara_search_items,
)

__all__ = [
    "HtmlAnchorSnapshot",
    "HtmlDocumentSnapshot",
    "BunjangCardParseResult",
    "parse_html_snapshot",
    "normalize_whitespace",
    "normalize_multiline_text",
    "normalize_price_text",
    "looks_like_time_line",
    "is_strict_price_line",
    "is_count_or_metric_line",
    "is_malformed_listing_title",
    "normalize_location_value",
    "extract_label_value",
    "extract_location_from_text",
    "extract_profile_name_from_aria_label",
    "pick_seller_candidate",
    "merge_item_metadata",
    "normalize_sale_status",
    "parse_bunjang_detail_payload",
    "normalize_url_for_match",
    "validate_platform_url",
    "extract_bunjang_product_id",
    "parse_bunjang_card_text",
    "parse_bunjang_search_items",
    "extract_numeric_article_id",
    "is_valid_joonggonara_title",
    "classify_joonggonara_candidate",
    "evaluate_scrape_quality",
    "parse_joonggonara_search_items",
    "parse_joonggonara_detail_text",
]
