"""PDF generator for Alkira opportunity briefs.

Uses fpdf2 (programmatic, pure Python). Mirrors the bento web layout
in a print-optimized form. See docs/superpowers/specs/2026-05-06-bento-brief-pdf-export-design.md.
"""

from __future__ import annotations

import re
from datetime import datetime

from fpdf import FPDF

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
    """Draw company hero with compact score badge in top-right corner.

    The score badge floats in the top-right; the company name + meta line
    occupy the left column. Meta text is full-width once it wraps below the
    badge zone so long pipe-delimited stat lines never collide with the badge.
    """
    x_left = 12.7
    page_w = 215.9 - 2 * 12.7  # 190.5mm content width
    y_start = pdf.get_y()
    badge_w = 50  # mm
    badge_h = 12  # approx total badge height (label + number + pills)
    badge_x = 215.9 - 12.7 - badge_w
    badge_y = y_start

    # ── Score badge (top-right) ───────────────────────────────
    pdf.set_xy(badge_x, badge_y)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(badge_w, 3, "ALKIRA FIT")

    pdf.set_xy(badge_x, badge_y + 4)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(*ALKIRA_INK)
    pdf.cell(15, 6, f"{score}/5")
    _draw_score_pills(pdf, score, badge_x + 16, badge_y + 7)

    # ── Company name (left, leaving room for the badge on row 1) ──
    name_w = badge_x - x_left - 4
    pdf.set_xy(x_left, y_start)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*ALKIRA_INK)
    pdf.cell(
        name_w, 10,
        _safe_text(company or "Untitled Brief"),
        new_x="LMARGIN", new_y="NEXT",
    )

    # ── Meta pills line ───────────────────────────────────────
    # Advance below whichever is taller: company name (10mm) or badge (~12mm).
    pdf.set_y(max(y_start + 10, badge_y + badge_h) + 1)
    pdf.set_x(x_left)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*ALKIRA_MUTED)
    cleaned = _strip_md((header_pills or "").strip())
    if cleaned:
        # Full width since we are now below the badge
        pdf.multi_cell(page_w, 5, _safe_text(cleaned))
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
    """Highlighted callout box for the recommended opening line.

    Two-pass render: first measure the actual wrapped line counts with
    fpdf2's ``dry_run=True, output="LINES"``, then paint the background + stripe to
    that exact height, then draw the text. This keeps the LISTENING FOR
    section inside the tinted box regardless of question length.
    """
    x = 12.7
    y_top = pdf.get_y()
    w = 190.5
    pad = 5.0
    stripe_w = 2.5
    inner_w = w - stripe_w - 2 * pad

    q_text = _safe_text(_strip_md(question or ""))
    lf_text = _safe_text(_strip_md(listening_for or ""))

    # ── Measure (split-only) ────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    q_lines = max(1, len(pdf.multi_cell(inner_w, 5, q_text, dry_run=True, output="LINES")))

    lf_lines = 0
    if lf_text:
        pdf.set_font("Helvetica", "", 9)
        lf_lines = max(1, len(pdf.multi_cell(inner_w, 4, lf_text, dry_run=True, output="LINES")))

    # Compose height: pad + OPENING(4) + 1 + (q_lines * 5) + (1 + 3.5 + lf_lines*4 if lf) + pad
    box_h = pad + 4 + 1 + (q_lines * 5)
    if lf_text:
        box_h += 1 + 3.5 + (lf_lines * 4)
    box_h += pad

    # ── Backgrounds ────────────────────────────────────────────
    pdf.set_fill_color(245, 248, 255)  # light blue tint
    pdf.rect(x, y_top, w, box_h, style="F")

    pdf.set_fill_color(*ALKIRA_ORANGE)
    pdf.rect(x, y_top, stripe_w, box_h, style="F")

    # ── Text ───────────────────────────────────────────────────
    pdf.set_xy(x + stripe_w + pad, y_top + pad)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ALKIRA_ORANGE)
    pdf.cell(inner_w, 4, "OPENING LINE", new_x="LMARGIN", new_y="NEXT")

    pdf.set_xy(x + stripe_w + pad, y_top + pad + 5)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*ALKIRA_INK)
    pdf.multi_cell(inner_w, 5, q_text)

    if lf_text:
        pdf.ln(1)
        pdf.set_x(x + stripe_w + pad)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*ALKIRA_BLUE)
        pdf.cell(inner_w, 3.5, "LISTENING FOR", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(x + stripe_w + pad)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*ALKIRA_INK)
        pdf.multi_cell(inner_w, 4, lf_text)

    # Advance past the box (use measured height — not cursor position, since
    # the cursor lands inside the box at end of text)
    pdf.set_y(y_top + box_h + 3)


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


def _draw_infra_grid_fullwidth(pdf: _BriefPDF, cells: dict) -> None:
    """Full-content-width 2x2 infrastructure grid (no score tile alongside)."""
    pdf.set_x(12.7)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*ALKIRA_BLUE)
    pdf.cell(0, 4, "INFRASTRUCTURE SNAPSHOT", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    x = 12.7
    y = pdf.get_y()
    w = 190.5
    h = 70  # taller since full width
    _draw_infra_grid(pdf, cells, x, y, w, h)
    pdf.set_y(y + h + 4)


# ── Infrastructure 2x2 grid ─────────────────────────────────────


def _draw_infra_grid(
    pdf: _BriefPDF,
    cells: dict,
    x: float,
    y: float,
    w: float,
    h: float,
) -> None:
    """Draw the 2x2 infrastructure cell grid.

    `cells` keys: cloud_platforms, on_prem, deployment, complexity.

    Body text is truncated based on the actual cell dimensions so long
    Resulting Complexity / Cloud Platforms strings never spill into Signals.
    """
    half_w = w / 2
    half_h = h / 2
    items = [
        ("CLOUD PLATFORMS", cells.get("cloud_platforms", ""), x, y),
        ("ON-PREM / HYBRID", cells.get("on_prem", ""), x + half_w, y),
        ("DEPLOYMENT MODEL", cells.get("deployment", ""), x, y + half_h),
        ("RESULTING COMPLEXITY", cells.get("complexity", ""), x + half_w, y + half_h),
    ]
    pad = 3.0

    # Body starts at cell_y + pad + 4.5 (after label) and ends at cell_y + half_h - pad.
    # Available height = half_h - 2*pad - 4.5. Line height = 3.6mm at 8pt.
    # Approx 35 chars/line in (half_w - 6mm) at 8pt Helvetica.
    available_h = half_h - 2 * pad - 4.5
    available_lines = max(1, int(available_h / 3.6))
    cell_chars_per_line = 35
    max_chars = available_lines * cell_chars_per_line

    for label, body, cx, cy in items:
        # Cell border
        pdf.set_draw_color(*ALKIRA_BORDER)
        pdf.set_line_width(0.2)
        pdf.set_fill_color(*ALKIRA_WHITE)
        pdf.rect(cx, cy, half_w, half_h, style="DF")

        # Label
        pdf.set_xy(cx + pad, cy + pad)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*ALKIRA_BLUE)
        pdf.cell(half_w - 2 * pad, 3.5, label)

        # Body — truncate to fit
        text = _strip_md((body or "—").strip())
        if len(text) > max_chars:
            text = text[: max_chars - 3].rstrip() + "..."

        pdf.set_xy(cx + pad, cy + pad + 4.5)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*ALKIRA_INK)
        pdf.multi_cell(half_w - 2 * pad, 3.6, _safe_text(text))


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
    pad = 3.5

    # Calculate max chars per tile body. Heading takes ~10mm, label ~5mm,
    # leaving ~80mm for body. Line height 3.5mm, ~38 chars/line at 8pt
    # in (tile_w - 7mm) ~= 56mm.
    body_h = tile_h - 25
    available_lines = max(1, int(body_h / 3.5))
    tile_chars_per_line = 38
    max_chars = available_lines * tile_chars_per_line

    for i, point in enumerate(points[:3]):
        cx = x + i * (tile_w + gap)
        # Tile background
        pdf.set_draw_color(*ALKIRA_BORDER)
        pdf.set_line_width(0.2)
        pdf.set_fill_color(*ALKIRA_WHITE)
        pdf.rect(cx, y, tile_w, tile_h, style="DF")

        # Orange top stripe
        pdf.set_fill_color(*ALKIRA_ORANGE)
        pdf.rect(cx, y, tile_w, 1.2, style="F")

        # Label
        pdf.set_xy(cx + pad, y + 3)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*ALKIRA_ORANGE)
        pdf.cell(tile_w - 2 * pad, 3.5, f"ENTRY 0{i+1}")

        # Heading
        pdf.set_xy(cx + pad, y + 7.5)
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

    # Lazy imports avoid circular dependency with app.py
    from app import (
        extract_company_header,
        extract_conversation_starters_structured,
        extract_entry_points,
        extract_infra_cells,
        extract_score,
        extract_section,
        first_sentences,
    )

    # ── Page 1 — Action (questions + opening callout) ───────────
    pdf.add_page()

    company_name, stats_line = extract_company_header(brief_md)
    if not company_name:
        company_name = company

    parsed_score, rationale = extract_score(brief_md)
    if not parsed_score:
        parsed_score = score

    _draw_hero_with_badge(pdf, company_name, stats_line, parsed_score)

    summary = first_sentences(rationale, max_chars=200)
    _draw_fit_summary(pdf, summary)

    starters_data = extract_conversation_starters_structured(brief_md)
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

    # ── Page 2 — Why (entry points + signals) ────────────────────
    pdf.add_page()

    points = extract_entry_points(brief_md)
    _draw_entry_points(pdf, points)

    signals = (
        extract_section(brief_md, "Signals & Timing")
        or extract_section(brief_md, "Signals and Timing")
    )
    _draw_signals(pdf, signals)

    # ── Page 3 — Appendix (infra + references) ───────────────────
    cells = extract_infra_cells(brief_md)
    refs = extract_section(brief_md, "References")
    if any(cells.values()) or refs.strip():
        pdf.add_page()
        if any(cells.values()):
            _draw_infra_grid_fullwidth(pdf, cells)
        _draw_references(pdf, refs)

    return bytes(pdf.output())
