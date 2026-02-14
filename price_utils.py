"""
Utilities for parsing and formatting Korean price strings.

Goal: keep price parsing consistent across scrapers/DB/UI and robust to common formats:
- "10,000원" -> 10000
- "10만", "10만원" -> 100000
- "1.2만" -> 12000
- "2만5천" -> 25000
- "무료", "나눔", "무료나눔" -> 0
"""

from __future__ import annotations

import re


_FREE_KEYWORDS = (
    "무료나눔",
    "무료",
    "나눔",
    "무나",
)


def parse_price_kr(text: str | None) -> int:
    """Parse a KRW price string into an integer amount in won. Returns 0 if unknown/unparseable."""
    if text is None:
        return 0

    s = str(text).strip()
    if not s:
        return 0

    s = s.replace(" ", "")
    s_lower = s.lower()

    # Normalize.
    s_norm = (
        s_lower.replace(",", "")
        .replace("krw", "")
        .replace("￦", "")
        .replace("원", "")
    )

    has_digits = bool(re.search(r"\d", s_norm))
    if not has_digits and any(k in s_norm for k in _FREE_KEYWORDS):
        return 0
    if s_norm in ("0", "0.0"):
        return 0

    total = 0

    # Handle "X만 ..." pattern first (most common for used markets).
    m_man = re.search(r"(\d+(?:\.\d+)?)만", s_norm)
    if m_man:
        try:
            total += int(float(m_man.group(1)) * 10_000)
        except Exception:
            return 0

        rest = s_norm[m_man.end() :]

        # "Y천" optionally exists.
        m_thousand = re.search(r"(\d+(?:\.\d+)?)천", rest)
        if m_thousand:
            try:
                total += int(float(m_thousand.group(1)) * 1_000)
            except Exception:
                pass
            return max(total, 0)

        # "2만5000" or "2만5" style tails.
        m_tail_digits = re.search(r"(\d+)", rest)
        if m_tail_digits:
            try:
                tail = int(m_tail_digits.group(1))
                # If the tail is short, treat it as "천" units (e.g. "2만5" -> 2만5천).
                if tail < 1000:
                    total += tail * 1000
                else:
                    total += tail
            except Exception:
                pass

        return max(total, 0)

    # Handle "X천" without "만".
    m_thousand_only = re.search(r"(\d+(?:\.\d+)?)천", s_norm)
    if m_thousand_only:
        try:
            return max(int(float(m_thousand_only.group(1)) * 1_000), 0)
        except Exception:
            return 0

    # Fallback: digits only (join all digit groups).
    digits = re.findall(r"\d+", s_norm)
    if not digits:
        return 0
    try:
        return max(int("".join(digits)), 0)
    except Exception:
        return 0


def format_price_kr(amount: int) -> str:
    """Format an integer KRW amount."""
    try:
        n = int(amount)
    except Exception:
        return ""
    if n <= 0:
        return "가격문의"
    return f"{n:,}원"
