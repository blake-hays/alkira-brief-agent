"""PDF generator for Alkira opportunity briefs.

Uses fpdf2 (programmatic, pure Python). Mirrors the bento web layout
in a print-optimized form. See docs/superpowers/specs/2026-05-06-bento-brief-pdf-export-design.md.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime

from fpdf import FPDF

# Bump this when changing PDF rendering. Streamlit's session-state cache
# uses it as part of the cache key so a code update invalidates stale PDFs.
PDF_VERSION = "v5"

# ── Brand palette (RGB tuples for fpdf2) ─────────────────────────
ALKIRA_BLUE   = (45, 88, 242)    # #2D58F2
ALKIRA_NAVY   = (10, 31, 68)     # #0A1F44
ALKIRA_INK    = (33, 31, 31)     # #211F1F
ALKIRA_MUTED  = (127, 127, 127)  # #7F7F7F
ALKIRA_ORANGE = (251, 146, 60)   # #FB923C
ALKIRA_AMBER  = (251, 191, 36)   # #FBBF24
ALKIRA_BORDER = (224, 231, 255)  # #E0E7FF
ALKIRA_WHITE  = (255, 255, 255)  # #FFFFFF


# ── Unicode → latin-1 sanitization ───────────────────────────────
# fpdf2's core Helvetica font is latin-1 only. Map common typographic
# characters to ASCII equivalents so any Unicode char in brief content
# (em-dashes, smart quotes, stars, bullets) renders cleanly.

_UNICODE_MAP = {
    "–": "-",     # en-dash –
    "—": "--",    # em-dash —
    "―": "--",    # horizontal bar ―
    "‘": "'",     # left single quote ‘
    "’": "'",     # right single quote ’
    "‚": ",",     # single low-9 quote ‚
    "“": '"',     # left double quote “
    "”": '"',     # right double quote ”
    "„": '"',     # double low-9 quote „
    "…": "...",   # horizontal ellipsis …
    "•": "-",     # bullet •
    "‣": "-",     # triangular bullet ‣
    "◦": "-",     # white bullet ◦
    "⁃": "-",     # hyphen bullet ⁃
    "→": "->",    # rightwards arrow →
    "←": "<-",    # leftwards arrow ←
    "★": "*",     # black star ★
    "☆": "-",     # white star ☆ (used as empty in our score)
    "✓": "v",     # check mark ✓
    "✗": "x",     # ballot x ✗
    " ": " ",     # non-breaking space
    "​": "",      # zero-width space
    " ": " ",     # thin space
    " ": " ",     # narrow no-break space
}


def _safe_text(s: str) -> str:
    """Map common Unicode chars to latin-1 equivalents for fpdf2 core fonts.

    Anything not in the map and not in latin-1 is replaced with a
    question mark (the latin-1 'replacement' fallback). This is a one-way
    sanitization — the goal is to never crash fpdf2 on user content.
    """
    if not s:
        return ""
    # Apply explicit map first
    for ch, replacement in _UNICODE_MAP.items():
        if ch in s:
            s = s.replace(ch, replacement)
    # Catch anything else not encodable in latin-1
    try:
        s.encode("latin-1")
        return s
    except UnicodeEncodeError:
        return s.encode("latin-1", errors="replace").decode("latin-1")


def _strip_md(s: str) -> str:
    r"""Strip basic inline markdown so PDF body text doesn't show literal markers.

    Handles ``**bold**``, ``__bold__``, ``*italic*``, ``_italic_``, ``\`code\```,
    and ``[text](url)`` (keeping just the link text). Also drops standalone
    horizontal rules (``---`` or ``***``) on their own lines, since the PDF
    has no equivalent visual primitive.
    """
    if not s:
        return ""
    # Strip **bold** and __bold__ -> bold
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"__(.+?)__", r"\1", s)
    # Strip *italic* and _italic_ -> italic (but not bare * that was used for bullets)
    s = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"\1", s)
    s = re.sub(r"(?<!_)_([^_\n]+?)_(?!_)", r"\1", s)
    # Strip `code` -> code
    s = re.sub(r"`([^`]+?)`", r"\1", s)
    # Strip [text](url) -> text  (the body doesn't render hyperlinks)
    s = re.sub(r"\[([^\]]+?)\]\([^)]+?\)", r"\1", s)
    # Strip standalone horizontal rules (--- or ***) on their own lines
    s = re.sub(r"^\s*[-*]{3,}\s*$", "", s, flags=re.MULTILINE)
    return s


# ── Filename helper ──────────────────────────────────────────────

_FILENAME_MAX = 40


def build_filename(company: str, period: str) -> str:
    """Build the PDF filename: AlkiraBrief_<sanitized-company>_<YYYY-MM>.pdf.

    Strips non-ASCII chars and punctuation (incl. underscores, our delimiter),
    replaces spaces with hyphens, truncates company to 40 chars. Falls back to
    "Company" sentinel for empty/all-punctuation/whitespace-only input.
    """
    cleaned = re.sub(r"[^A-Za-z0-9\s-]", "", company)   # ASCII-only, drop punctuation + underscores
    cleaned = re.sub(r"\s+", "-", cleaned.strip())      # spaces → hyphens
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")    # collapse hyphens
    if not cleaned:
        cleaned = "Company"
    if len(cleaned) > _FILENAME_MAX:
        cleaned = cleaned[:_FILENAME_MAX].rstrip("-")
    return f"AlkiraBrief_{cleaned}_{period}.pdf"


# ── PDF subclass with branded header + footer ──────────────────


class _BriefPDF(FPDF):
    """fpdf2 subclass with Alkira-branded header and footer on every page."""

    def __init__(self, generated_at: datetime):
        super().__init__(orientation="P", unit="mm", format="Letter")
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(left=12.7, top=20, right=12.7)  # 0.5"
        self.generated_at = generated_at
        self.alias_nb_pages()  # enables {nb} for total page count

    def header(self) -> None:  # noqa: D401  (fpdf hook)
        # Wordmark left
        self.set_xy(12.7, 8)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*ALKIRA_INK)
        self.cell(40, 6, "ALKIRA")

        # Confidential + month-year right
        self.set_xy(-80, 8)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*ALKIRA_MUTED)
        period = self.generated_at.strftime("%B %Y").upper()
        self.cell(0, 6, f"CONFIDENTIAL  |  {period}", align="R")

        # Hairline rule
        self.set_draw_color(*ALKIRA_BORDER)
        self.set_line_width(0.2)
        self.line(12.7, 16, 215.9 - 12.7, 16)

        # Move below header
        self.set_y(22)

    def footer(self) -> None:  # noqa: D401  (fpdf hook)
        self.set_y(-15)
        # Hairline
        self.set_draw_color(*ALKIRA_BORDER)
        self.set_line_width(0.2)
        self.line(12.7, self.get_y(), 215.9 - 12.7, self.get_y())

        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*ALKIRA_MUTED)
        self.cell(0, 4, f"Page {self.page_no()} of {{nb}}")
        self.set_y(-12)
        self.cell(
            0, 4,
            f"Generated {self.generated_at.strftime('%Y-%m-%d')}",
            align="R",
        )


# ── Hero block with score badge ─────────────────────────────────


def _draw_score_pills(
    pdf: _BriefPDF,
    score: int,
    x: float,
    y: float,
    pill_w: float = 4.0,
    pill_h: float = 3.0,
    gap: float = 1.0,
) -> float:
    """Draw 5 small horizontal pills representing the score. Returns total width."""
    clamped = max(0, min(5, score))
    for i in range(5):
        cx = x + i * (pill_w + gap)
        if i < clamped:
            pdf.set_fill_color(*ALKIRA_ORANGE)
        else:
            pdf.set_fill_color(220, 220, 220)  # light gray
        pdf.rect(cx, y, pill_w, pill_h, style="F")
    return 5 * pill_w + 4 * gap


def _draw_hero_with_badge(
    pdf: _BriefPDF,
    company: str,
    header_pills: str,
    score: int,
) -> None:
    """Draw company hero with a compact score eyebrow above the company name.

    Layout (top to bottom):
        Row 1: ``ALKIRA FIT  4/5  ██░`` eyebrow, right-aligned
        Row 2: Company name, full width, no horizontal collision risk
        Row 3: Meta pills line, full width
    """
    x_left = 12.7
    page_w = 215.9 - 2 * 12.7  # 190.5mm content width
    y_start = pdf.get_y()

    # ── Row 1: Score eyebrow (small, right-aligned) ───────────
    # Total eyebrow width: "ALKIRA FIT" label + "4/5" + pills
    pill_block_w = 5 * 4 + 4 * 1  # 5 pills × 4mm + 4 gaps × 1mm = 24mm
    eyebrow_y = y_start
    pills_x = 215.9 - 12.7 - pill_block_w
    score_x = pills_x - 12  # space for "4/5"
    label_x = score_x - 22  # space for "ALKIRA FIT"

    pdf.set_xy(label_x, eyebrow_y)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(20, 4, "ALKIRA FIT", align="R")

    pdf.set_xy(score_x, eyebrow_y - 0.5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*ALKIRA_INK)
    pdf.cell(10, 4, f"{score}/5", align="R")

    _draw_score_pills(pdf, score, pills_x, eyebrow_y + 0.5)

    # ── Row 2: Company name, full width ───────────────────────
    pdf.set_xy(x_left, y_start + 6)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(*ALKIRA_INK)
    pdf.multi_cell(
        page_w, 9,
        _safe_text(company or "Untitled Brief"),
    )

    # ── Row 3: Meta pills line ────────────────────────────────
    pdf.set_x(x_left)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*ALKIRA_MUTED)
    cleaned = _strip_md((header_pills or "").strip())
    if cleaned:
        pdf.multi_cell(page_w, 4.5, _safe_text(cleaned))
    pdf.ln(4)


def _draw_fit_summary(pdf: _BriefPDF, summary: str) -> None:
    """One-sentence fit summary positioned under the hero."""
    if not summary or not summary.strip():
        return
    pdf.set_x(12.7)
    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(*ALKIRA_INK)
    pdf.multi_cell(190.5, 5, _safe_text(_strip_md(summary)))
    pdf.ln(3)


def _draw_stakeholders_line(pdf: _BriefPDF, stakeholders: str) -> None:
    """Render the stakeholders one-liner with a small label."""
    if not stakeholders or not stakeholders.strip():
        return
    pdf.set_x(12.7)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(0, 4, "STAKEHOLDERS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(12.7)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*ALKIRA_INK)
    pdf.multi_cell(190.5, 5, _safe_text(_strip_md(stakeholders)))
    pdf.ln(3)


def _draw_opening_callout(
    pdf: _BriefPDF,
    question: str,
    listening_for: str,
) -> None:
    """Opening line callout — orange left stripe, no background fill.

    The question is set off by a thick orange vertical rule on the left
    and generous whitespace, not by a contained box. Content renders
    first so the stripe can match the actual content height.
    """
    x = 12.7
    y_start = pdf.get_y()
    stripe_w = 2.0
    text_x = x + stripe_w + 6  # 6mm gap after stripe
    text_w = 215.9 - 12.7 - (text_x - x)  # right margin = 12.7

    # OPENING LINE label
    pdf.set_xy(text_x, y_start)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ALKIRA_ORANGE)
    pdf.cell(text_w, 4, "OPENING LINE")

    # Question text — bigger, bolder
    pdf.set_xy(text_x, y_start + 5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*ALKIRA_INK)
    pdf.multi_cell(text_w, 5.5, _safe_text(_strip_md(question)))

    # Listening for
    pdf.ln(1)
    pdf.set_x(text_x)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(text_w, 3.5, "LISTENING FOR")
    pdf.ln(4)
    pdf.set_x(text_x)
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*ALKIRA_INK)
    pdf.multi_cell(text_w, 4.2, _safe_text(_strip_md(listening_for)))

    y_end = pdf.get_y()

    # Now draw the orange stripe — height = actual content height
    pdf.set_fill_color(*ALKIRA_ORANGE)
    pdf.rect(x, y_start, stripe_w, y_end - y_start, style="F")

    pdf.ln(5)


def _draw_followup_questions(pdf: _BriefPDF, questions: list[dict]) -> None:
    """Render the remaining (non-opener) questions as a compact list."""
    if not questions:
        return
    pdf.set_x(12.7)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(0, 4, "FOLLOW-UP QUESTIONS", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    for q in questions:
        pdf.set_x(12.7)
        # Question number + text
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*ALKIRA_INK)
        question_text = f"{q.get('number', '?')}. {_strip_md(q.get('question', ''))}"
        pdf.multi_cell(190.5, 5, _safe_text(question_text))

        listening = (q.get("listening_for") or "").strip()
        if listening:
            pdf.set_x(16)
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*ALKIRA_MUTED)
            pdf.multi_cell(186, 4, _safe_text("Listening for: " + _strip_md(listening)))
        pdf.ln(1.5)

    pdf.ln(2)  # Extra space before next section


def _draw_validate_early(pdf: _BriefPDF, bullets: list[str]) -> None:
    """Render Validate Early bullets."""
    if not bullets:
        return
    pdf.set_x(12.7)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(0, 4, "VALIDATE EARLY", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.5)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*ALKIRA_INK)
    for b in bullets:
        pdf.set_x(15)
        pdf.cell(3, 4, "-")
        pdf.multi_cell(180, 4, _safe_text(_strip_md(b)))
    pdf.ln(2)


def _draw_infra_list(pdf: _BriefPDF, cells: dict) -> None:
    """Flow-based infrastructure list. No absolute Y positioning.

    Renders each cell as an inline LABEL + body paragraph, single-column,
    so the auto page-break works cleanly and labels never get separated
    from their body content across page boundaries.
    """
    if not any(cells.values()):
        return

    # Section header
    pdf.set_x(12.7)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(0, 4, "INFRASTRUCTURE SNAPSHOT", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    items = [
        ("CLOUD PLATFORMS", cells.get("cloud_platforms", "")),
        ("ON-PREM / HYBRID", cells.get("on_prem", "")),
        ("DEPLOYMENT MODEL", cells.get("deployment", "")),
        ("RESULTING COMPLEXITY", cells.get("complexity", "")),
    ]

    for label, body in items:
        body = (body or "").strip()
        if not body:
            continue

        # Inline label
        pdf.set_x(12.7)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*ALKIRA_BLUE)
        pdf.cell(0, 3.5, label, new_x="LMARGIN", new_y="NEXT")

        # Body
        pdf.set_x(12.7)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*ALKIRA_INK)
        body_clean = _strip_md(body)
        if len(body_clean) > 400:
            body_clean = body_clean[:397].rstrip() + "..."
        pdf.multi_cell(190.5, 4, _safe_text(body_clean))
        pdf.ln(2)


# ── Signals & References tiles ──────────────────────────────────


def _draw_signals(pdf: _BriefPDF, signals_md: str) -> None:
    """Draw the Signals & Timing tile (full width, white)."""
    if not signals_md.strip():
        return

    w = 190.5

    # Section label
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(0, 5, "SIGNALS & TIMING", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # Bullets — strip "- " or "* " from each line
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*ALKIRA_INK)
    for raw in signals_md.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = _strip_md(line)
        if not line:
            continue  # skip lines that became empty after stripping (e.g., ---)
        pdf.set_x(15)
        pdf.cell(3, 4.5, "-")
        pdf.multi_cell(w - 5, 4.5, _safe_text(line))
    pdf.ln(2)


def _draw_references(pdf: _BriefPDF, refs_md: str) -> None:
    """Draw the References tile at the end of the brief.

    Left-aligned (not justified) so URLs and citation numbers don't get
    stretched. Drops any stray ``*CONFIDENTIAL*`` footer line that some
    briefs append below their references.
    """
    if not refs_md.strip():
        return

    pdf.ln(2)
    pdf.set_x(12.7)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(0, 5, "REFERENCES", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*ALKIRA_INK)
    for raw in refs_md.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Skip the stray "*CONFIDENTIAL*" footer some briefs include
        if re.sub(r"[\*\s]", "", line).upper() == "CONFIDENTIAL":
            continue
        line = _strip_md(line)
        if not line:
            continue
        # Lines look like "[1] Description -- https://..."
        pdf.set_x(12.7)
        pdf.multi_cell(0, 4, _safe_text(line), align="L")


# ── Three Alkira Entry Points (3-column row) ────────────────────


def _draw_entry_points(pdf: _BriefPDF, points: list[dict]) -> None:
    """Draw the 3 entry-point tiles in a row, each with orange top stripe.

    Body text is rendered as a single combined paragraph rather than
    Signal/Solution/Proof sub-labels. This is more reliable across brief
    formats — if labeled fields are empty we fall back to the raw body.

    The caller is responsible for starting a new page if desired; this
    helper renders inline at the current y-cursor.
    """
    if not points:
        return

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(0, 5, "THREE ALKIRA ENTRY POINTS", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    x = 12.7
    y = pdf.get_y()
    content_w = 190.5
    gap = 3.0
    tile_w = (content_w - 2 * gap) / 3
    tile_h = 95  # was 75 — more room for combined body content
    pad = 1.5  # was 3.5 — let content breathe to natural column edges

    # Calculate max chars per tile body. Heading takes ~10mm, label ~5mm,
    # leaving ~80mm for body. Line height 3.5mm, ~38 chars/line at 8pt
    # in (tile_w - 7mm) ~= 56mm.
    body_h = tile_h - 25
    available_lines = max(1, int(body_h / 3.5))
    tile_chars_per_line = 38
    max_chars = available_lines * tile_chars_per_line

    for i, point in enumerate(points[:3]):
        cx = x + i * (tile_w + gap)
        # Orange top stripe only — no border, no fill
        pdf.set_fill_color(*ALKIRA_ORANGE)
        pdf.rect(cx, y, tile_w, 1.2, style="F")

        # Label
        pdf.set_xy(cx + pad, y + 4.5)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*ALKIRA_ORANGE)
        pdf.cell(tile_w - 2 * pad, 3.5, f"ENTRY 0{i+1}")

        # Heading
        pdf.set_xy(cx + pad, y + 9)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*ALKIRA_INK)
        heading = _strip_md(point.get("heading", ""))[:80]
        pdf.multi_cell(tile_w - 2 * pad, 4.5, _safe_text(heading))

        # Body — combine all available content into a single paragraph.
        # Try labeled fields first; if all are empty, fall back to raw body.
        signal = (point.get("signal") or "").strip()
        solution = (point.get("solution") or "").strip()
        proof = (point.get("proof") or "").strip()
        body_raw = (point.get("body") or "").strip()

        if solution or proof:
            # Combine into one paragraph (no Signal/Solution/Proof chrome
            # for a compact, readable look)
            parts = [p for p in [signal, solution, proof] if p]
            body_text = " ".join(parts)
        elif signal:
            body_text = signal
        else:
            body_text = body_raw

        body_text = _strip_md(body_text)
        if len(body_text) > max_chars:
            body_text = body_text[: max_chars - 3].rstrip() + "..."

        if body_text:
            cy = pdf.get_y() + 1
            pdf.set_xy(cx + pad, cy)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(*ALKIRA_INK)
            pdf.multi_cell(tile_w - 2 * pad, 3.5, _safe_text(body_text))

    # Move below the row
    pdf.set_y(y + tile_h + 4)


# ── Public API ──────────────────────────────────────────────────


def generate_brief_pdf(
    brief_md: str,
    company: str,
    score: int,
    generated_at: datetime | None = None,
) -> bytes:
    """Render brief markdown as a print-optimized PDF for sales reps.

    Page ordering is action-first: Page 1 surfaces the actionable
    Conversation Starters content (opening line callout + follow-up
    questions + Validate Early bullets). Page 2 covers the three Alkira
    entry points and Signals & Timing. Page 3 (only if content) is the
    Infrastructure Snapshot + References appendix.
    """
    when = generated_at or datetime.now()
    pdf = _BriefPDF(generated_at=when)

    # Lazy imports avoid circular dependency with app.py.
    # Stale Streamlit Cloud deploys can have an older `app` module cached in
    # sys.modules without the newer helpers — degrade gracefully if missing.
    from app import (
        extract_company_header,
        extract_entry_points,
        extract_infra_cells,
        extract_score,
        extract_section,
    )
    try:
        from app import extract_conversation_starters_structured
    except ImportError:
        def extract_conversation_starters_structured(_brief: str) -> dict:
            return {
                "stakeholders": "",
                "best_first_hint": "",
                "best_first_index": 1,
                "questions": [],
                "validate_early": [],
            }
    try:
        from app import first_sentences
    except ImportError:
        def first_sentences(text: str, max_chars: int = 200) -> str:
            text = (text or "").strip()
            return text if len(text) <= max_chars else text[: max_chars - 3].rstrip() + "..."

    # ── Page 1 — Action (questions + opening callout) ───────────
    pdf.add_page()

    company_name, stats_line = extract_company_header(brief_md)
    if not company_name:
        company_name = company

    parsed_score, rationale = extract_score(brief_md)
    if not parsed_score:
        parsed_score = score

    _draw_hero_with_badge(pdf, company_name, stats_line, parsed_score)

    starters_data = extract_conversation_starters_structured(brief_md)
    if not starters_data["questions"]:
        section_chars = len(extract_section(brief_md, "Conversation Starters"))
        print(
            f"[pdf] WARNING: No conversation starters parsed for brief. "
            f"Section length: {section_chars} chars",
            file=sys.stderr,
        )
    _draw_stakeholders_line(pdf, starters_data["stakeholders"])

    questions = starters_data["questions"]
    best_idx = starters_data["best_first_index"]
    if questions:
        best_q = next(
            (q for q in questions if q["number"] == best_idx),
            questions[0],
        )
        _draw_opening_callout(
            pdf,
            best_q.get("question", ""),
            best_q.get("listening_for", ""),
        )
        remaining = [q for q in questions if q["number"] != best_q["number"]]
        _draw_followup_questions(pdf, remaining)

    _draw_validate_early(pdf, starters_data["validate_early"])

    # ── Why (entry points + signals) — flows naturally, no forced page break ──
    points = extract_entry_points(brief_md)
    _draw_entry_points(pdf, points)

    signals = (
        extract_section(brief_md, "Signals & Timing")
        or extract_section(brief_md, "Signals and Timing")
    )
    _draw_signals(pdf, signals)

    # ── Appendix (infra + references) — flows naturally ──
    cells = extract_infra_cells(brief_md)
    refs = extract_section(brief_md, "References")
    if any(cells.values()):
        _draw_infra_list(pdf, cells)
    if refs.strip():
        _draw_references(pdf, refs)

    return bytes(pdf.output())
