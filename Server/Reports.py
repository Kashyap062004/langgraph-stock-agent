import io
import os
import re
import smtplib

from datetime import datetime
from zoneinfo import ZoneInfo

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# StockSense AI Theme
# ============================================================

NAVY = colors.HexColor("#0F172A")
NAVY_LIGHT = colors.HexColor("#1E293B")

CYAN = colors.HexColor("#13CFE3")
CYAN_DARK = colors.HexColor("#0891B2")
CYAN_LIGHT = colors.HexColor("#E6FAFD")

TEXT = colors.HexColor("#0F172A")
TEXT_MUTED = colors.HexColor("#64748B")

BORDER = colors.HexColor("#E2E8F0")
PAGE_BG = colors.HexColor("#F8FAFC")
WHITE = colors.white

TABLE_ALT = colors.HexColor("#F8FAFC")


# ============================================================
# Markdown → ReportLab inline formatting
# ============================================================

def _inline_markdown_to_html(text: str) -> str:
    """
    Convert the markdown formatting used by the StockSense AI
    response into ReportLab-compatible markup.

    Supported:
        **bold**
        *italic*
    """

    # Escape HTML characters first
    text = (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    # Bold: **text**
    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text,
    )

    # Italic: *text*
    text = re.sub(
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
        r"<i>\1</i>",
        text,
    )

    return text


# ============================================================
# Markdown table parser
# ============================================================

def _parse_table_block(lines: list[str]) -> list[list[str]]:
    """
    Parse markdown pipe tables.

    Example:

        | Metric | GOOGL | NVDA |
        |--------|-------|------|
        | Price  | $340  | $216 |

    becomes:

        [
            ["Metric", "GOOGL", "NVDA"],
            ["Price", "$340", "$216"]
        ]
    """

    rows = []

    for line in lines:
        stripped = line.strip().strip("|")

        if not stripped:
            continue

        cells = [cell.strip() for cell in stripped.split("|")]

        # Ignore markdown separator row.
        #
        # Examples:
        # ---
        # :---
        # ---:
        # :---:
        if all(
            re.fullmatch(r":?-+:?", cell)
            for cell in cells
            if cell
        ):
            continue

        rows.append(cells)

    return rows


# ============================================================
# Page Header / Footer
# ============================================================

def _draw_page_header_footer(canvas, doc):
    """
    Draw StockSense AI branding on every page.
    """

    canvas.saveState()

    page_width, page_height = letter

    # ========================================================
    # Background
    # ========================================================

    canvas.setFillColor(PAGE_BG)

    canvas.rect(
        0,
        0,
        page_width,
        page_height,
        fill=1,
        stroke=0,
    )

    # ========================================================
    # TOP HEADER
    # ========================================================

    header_x = 0.35 * inch
    header_y = page_height - 0.55 * inch
    header_width = page_width - 0.70 * inch
    header_height = 0.32 * inch

    canvas.setFillColor(NAVY)

    canvas.roundRect(
        header_x,
        header_y,
        header_width,
        header_height,
        0.07 * inch,
        fill=1,
        stroke=0,
    )

    # --------------------------------------------------------
    # Cyan logo square
    # --------------------------------------------------------

    logo_x = header_x + 0.09 * inch
    logo_y = header_y + 0.055 * inch

    canvas.setFillColor(CYAN)

    canvas.roundRect(
        logo_x,
        logo_y,
        0.20 * inch,
        0.20 * inch,
        0.04 * inch,
        fill=1,
        stroke=0,
    )

    # Small logo icon
    canvas.setFillColor(NAVY)

    canvas.setFont(
        "Helvetica-Bold",
        8,
    )

    canvas.drawCentredString(
        logo_x + 0.10 * inch,
        logo_y + 0.065 * inch,
        "↗",
    )

    # --------------------------------------------------------
    # Brand name
    # --------------------------------------------------------

    canvas.setFillColor(WHITE)

    canvas.setFont(
        "Helvetica-Bold",
        8.5,
    )

    canvas.drawString(
        header_x + 0.38 * inch,
        header_y + 0.105 * inch,
        "StockSense AI",
    )

    # --------------------------------------------------------
    # Header right text
    # --------------------------------------------------------

    canvas.setFillColor(
        colors.HexColor("#CBD5E1")
    )

    canvas.setFont(
        "Helvetica",
        7,
    )

    canvas.drawRightString(
        header_x + header_width - 0.10 * inch,
        header_y + 0.105 * inch,
        "Market Intelligence Report",
    )

    # ========================================================
    # FOOTER
    # ========================================================

    footer_line_y = 0.47 * inch

    canvas.setStrokeColor(BORDER)

    canvas.setLineWidth(0.6)

    canvas.line(
        0.55 * inch,
        footer_line_y,
        page_width - 0.55 * inch,
        footer_line_y,
    )

    # Footer left

    canvas.setFillColor(TEXT_MUTED)

    canvas.setFont(
        "Helvetica",
        6.8,
    )

    canvas.drawString(
        0.55 * inch,
        0.29 * inch,
        "StockSense AI • Verify important figures before trading.",
    )

    # Footer right

    canvas.drawRightString(
        page_width - 0.55 * inch,
        0.29 * inch,
        f"Page {canvas.getPageNumber()}",
    )

    canvas.restoreState()


# ============================================================
# PDF GENERATOR
# ============================================================

def markdown_to_pdf(
    content: str,
    title: str = "Stock Report",
) -> bytes:
    """
    Convert StockSense AI markdown content into a professional PDF.

    Returns:
        bytes: Raw PDF data
    """

    buffer = io.BytesIO()

    # ========================================================
    # Document
    # ========================================================

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,

        # Header space
        topMargin=0.82 * inch,

        # Footer space
        bottomMargin=0.65 * inch,

        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,

        title=title,
        author="StockSense AI",
        subject="Market Intelligence Report",
    )

    styles = getSampleStyleSheet()

    # ========================================================
    # Styles
    # ========================================================

    # --------------------------------------------------------
    # Hero title
    # --------------------------------------------------------

    hero_title_style = ParagraphStyle(
        "HeroTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        textColor=WHITE,
        alignment=TA_LEFT,
        spaceAfter=4,
    )

    # --------------------------------------------------------
    # Hero subtitle
    # --------------------------------------------------------

    hero_subtitle_style = ParagraphStyle(
        "HeroSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#94A3B8"),
        spaceAfter=0,
    )

    # --------------------------------------------------------
    # Main heading
    # --------------------------------------------------------

    h1_style = ParagraphStyle(
        "ReportH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=NAVY,
        spaceBefore=8,
        spaceAfter=8,
    )

    # --------------------------------------------------------
    # Section heading
    # --------------------------------------------------------

    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=16,
        textColor=NAVY,
        spaceBefore=12,
        spaceAfter=6,
    )

    # --------------------------------------------------------
    # Subsection heading
    # --------------------------------------------------------

    h3_style = ParagraphStyle(
        "ReportH3",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=NAVY_LIGHT,
        spaceBefore=8,
        spaceAfter=5,
    )

    # --------------------------------------------------------
    # Normal text
    # --------------------------------------------------------

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.2,
        leading=14,
        textColor=TEXT,
        spaceAfter=6,
    )

    # --------------------------------------------------------
    # Bullet text
    # --------------------------------------------------------

    bullet_style = ParagraphStyle(
        "ReportBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=TEXT,
        leftIndent=10,
        firstLineIndent=0,
        spaceAfter=4,
    )

    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata_style = ParagraphStyle(
        "Metadata",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=11,
        textColor=TEXT_MUTED,
    )

    # --------------------------------------------------------
    # Table cell
    # --------------------------------------------------------

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11,
        textColor=TEXT,
    )

    # --------------------------------------------------------
    # Table header
    # --------------------------------------------------------

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.2,
        leading=11,
        textColor=WHITE,
    )

    # --------------------------------------------------------
    # Table important value
    # --------------------------------------------------------

    table_value_style = ParagraphStyle(
        "TableValue",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.2,
        leading=11,
        textColor=TEXT,
    )

    # ========================================================
    # Elements
    # ========================================================

    elements = []

    # ========================================================
    # Report title / hero card
    # ========================================================

    generated_at = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime(
        "%B %d, %Y at %I:%M %p IST"
    )

    hero_title = Paragraph(
        _inline_markdown_to_html(title),
        hero_title_style,
    )

    hero_subtitle = Paragraph(
        "AI-powered market analysis, fundamentals & insights",
        hero_subtitle_style,
    )

    hero_left = [
        hero_title,
        Spacer(1, 4),
        hero_subtitle,
    ]

    hero_brand_style = ParagraphStyle(
        "HeroBrand",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=CYAN,
        spaceAfter=2,
    )

    hero_report_style = ParagraphStyle(
        "HeroReport",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=WHITE,
    )

    hero_right = [
        Paragraph(
            "STOCKSENSE AI",
            hero_brand_style,
        ),
        Paragraph(
            "MARKET REPORT",
            hero_report_style,
        ),
    ]

    hero_table = Table(
        [[hero_left, hero_right]],
        colWidths=[
            5.05 * inch,
            1.45 * inch,
        ],
    )

    hero_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    NAVY,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),

                (
                    "ALIGN",
                    (1, 0),
                    (1, 0),
                    "RIGHT",
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (0, 0),
                    14,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (0, 0),
                    8,
                ),

                (
                    "LEFTPADDING",
                    (1, 0),
                    (1, 0),
                    8,
                ),

                (
                    "RIGHTPADDING",
                    (1, 0),
                    (1, 0),
                    14,
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    12,
                ),
            ]
        )
    )

    elements.append(hero_table)

    elements.append(
        Spacer(1, 10)
    )

    # ========================================================
    # Metadata card
    # ========================================================

    metadata_label_style = ParagraphStyle(
        "MetadataLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.4,
        leading=9,
        textColor=NAVY,
        spaceAfter=2,
    )

    metadata_value_style = ParagraphStyle(
        "MetadataValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.6,
        leading=10,
        textColor=TEXT_MUTED,
    )

    def metadata_cell(label, value):
        return [
            Paragraph(
                label,
                metadata_label_style,
            ),
            Paragraph(
                value,
                metadata_value_style,
            ),
        ]

    metadata_table = Table(
        [[
            metadata_cell(
                "Generated",
                generated_at,
            ),
            metadata_cell(
                "Platform",
                "StockSense AI",
            ),
            metadata_cell(
                "Report Type",
                "Market Intelligence",
            ),
        ]],
        colWidths=[
            2.25 * inch,
            1.95 * inch,
            2.30 * inch,
    ],
    )

    metadata_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    WHITE,
                ),

                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    BORDER,
                ),

                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    BORDER,
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    elements.append(metadata_table)

    elements.append(
        Spacer(1, 12)
    )


    lines = content.splitlines()

    i = 0

    bullet_buffer: list[str] = []


    def flush_bullets():
        """
        Render markdown bullets as clean dash bullets.

        IMPORTANT:
        We intentionally do NOT use ListFlowable because
        some ReportLab/font combinations render bullet glyphs
        as blobs/squares.
        """

        if not bullet_buffer:
            return

        for item in bullet_buffer:

            bullet_html = _inline_markdown_to_html(
                item
            )

            bullet_paragraph = Paragraph(
                f'<font color="#0891B2"><b>–</b></font>'
                f'&nbsp;&nbsp;{bullet_html}',
                bullet_style,
            )

            elements.append(
                bullet_paragraph
            )

        elements.append(
            Spacer(1, 3)
        )

        bullet_buffer.clear()



    while i < len(lines):

        line = lines[i]

        stripped = line.strip()

        if not stripped:

            flush_bullets()

            i += 1

            continue


        if stripped.startswith("#"):

            flush_bullets()

            level = len(
                stripped
            ) - len(
                stripped.lstrip("#")
            )

            text = (
                stripped
                .lstrip("#")
                .strip()
            )

            html_text = _inline_markdown_to_html(
                text
            )

            # H1
            if level == 1:

                elements.append(
                    Paragraph(
                        html_text,
                        h1_style,
                    )
                )

            # H2
            elif level == 2:

                elements.append(
                    Paragraph(
                        html_text,
                        h2_style,
                    )
                )

            # H3+
            else:

                elements.append(
                    Paragraph(
                        html_text,
                        h3_style,
                    )
                )

         

            if level >= 2:

                accent_table = Table(
                    [[""]],
                    colWidths=[
                        0.55 * inch
                    ],
                    rowHeights=[
                        0.025 * inch
                    ],
                )

                accent_table.setStyle(
                    TableStyle(
                        [
                            (
                                "BACKGROUND",
                                (0, 0),
                                (-1, -1),
                                CYAN,
                            ),

                            (
                                "LEFTPADDING",
                                (0, 0),
                                (-1, -1),
                                0,
                            ),

                            (
                                "RIGHTPADDING",
                                (0, 0),
                                (-1, -1),
                                0,
                            ),

                            (
                                "TOPPADDING",
                                (0, 0),
                                (-1, -1),
                                0,
                            ),

                            (
                                "BOTTOMPADDING",
                                (0, 0),
                                (-1, -1),
                                0,
                            ),
                        ]
                    )
                )

                elements.append(
                    accent_table
                )

                elements.append(
                    Spacer(1, 4)
                )

            i += 1

            continue


        if stripped.startswith("|"):

            flush_bullets()

            table_lines = []

            while (
                i < len(lines)
                and lines[i].strip().startswith("|")
            ):

                table_lines.append(
                    lines[i]
                )

                i += 1

            rows = _parse_table_block(
                table_lines
            )

            if not rows:
                continue

            # ------------------------------------------------
            # Normalize row sizes
            # ------------------------------------------------

            max_cols = max(
                len(row)
                for row in rows
            )

            normalized_rows = []

            for row in rows:

                normalized_rows.append(
                    row
                    + [""] * (
                        max_cols
                        - len(row)
                    )
                )

            # ------------------------------------------------
            # Convert cells to Paragraph
            # ------------------------------------------------

            wrapped_rows = []

            for row_index, row in enumerate(
                normalized_rows
            ):

                formatted_row = []

                for cell in row:

                    html_cell = (
                        _inline_markdown_to_html(
                            cell
                        )
                    )

                    # Make numeric/price values bold
                    if (
                        row_index > 0
                        and re.search(
                            r"[$₹€£]\s?[\d,.]+|"
                            r"\b\d+(?:\.\d+)?%",
                            cell,
                        )
                    ):

                        cell_style = (
                            table_value_style
                        )

                    elif row_index == 0:

                        cell_style = (
                            table_header_style
                        )

                    else:

                        cell_style = (
                            table_cell_style
                        )

                    formatted_row.append(
                        Paragraph(
                            html_cell,
                            cell_style,
                        )
                    )

                wrapped_rows.append(
                    formatted_row
                )

            # ------------------------------------------------
            # Create table
            # ------------------------------------------------

            table_width = 6.5 * inch

            col_width = (
                table_width / max_cols
            )

            table = Table(
                wrapped_rows,
                colWidths=[
                    col_width
                ] * max_cols,
                repeatRows=1,
            )

            # ------------------------------------------------
            # Table styling
            # ------------------------------------------------

            table.setStyle(
                TableStyle(
                    [
                        # Header background
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            NAVY,
                        ),

                        # Header text
                        (
                            "TEXTCOLOR",
                            (0, 0),
                            (-1, 0),
                            WHITE,
                        ),

                        # Cyan header line
                        (
                            "LINEBELOW",
                            (0, 0),
                            (-1, 0),
                            2,
                            CYAN,
                        ),

                        # Outer grid
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.45,
                            BORDER,
                        ),

                        # Alternating rows
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-1, -1),
                            [
                                WHITE,
                                TABLE_ALT,
                            ],
                        ),

                        # Vertical alignment
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "MIDDLE",
                        ),

                        # Cell padding
                        (
                            "TOPPADDING",
                            (0, 0),
                            (-1, -1),
                            7,
                        ),

                        (
                            "BOTTOMPADDING",
                            (0, 0),
                            (-1, -1),
                            7,
                        ),

                        (
                            "LEFTPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),

                        (
                            "RIGHTPADDING",
                            (0, 0),
                            (-1, -1),
                            8,
                        ),
                    ]
                )
            )

            elements.append(
                table
            )

            elements.append(
                Spacer(1, 10)
            )

            continue

        # ----------------------------------------------------
        # Bullet
        #
        # Supports:
        #   - text
        #   * text
        # ----------------------------------------------------

        if (
            stripped.startswith("- ")
            or stripped.startswith("* ")
        ):

            bullet_buffer.append(
                stripped[2:].strip()
            )

            i += 1

            continue

        # ----------------------------------------------------
        # Normal paragraph
        # ----------------------------------------------------

        flush_bullets()

        elements.append(
            Paragraph(
                _inline_markdown_to_html(
                    stripped
                ),
                body_style,
            )
        )

        i += 1

    # Flush anything remaining
    flush_bullets()

    # ========================================================
    # Build PDF
    # ========================================================

    doc.build(
        elements,
        onFirstPage=_draw_page_header_footer,
        onLaterPages=_draw_page_header_footer,
    )

    return buffer.getvalue()


# ============================================================
# Email Report
# ============================================================

def send_report_email(
    to_email: str,
    subject: str,
    pdf_bytes: bytes,
    pdf_filename: str,
    body_text: str = (
        "Your requested StockSense AI "
        "market report is attached."
    ),
) -> None:
    """
    Send generated PDF using SMTP.
    """

    # --------------------------------------------------------
    # Read SMTP configuration
    # --------------------------------------------------------

    smtp_host = os.environ.get(
        "SMTP_HOST"
    )

    smtp_port = int(
        os.environ.get(
            "SMTP_PORT",
            "587",
        )
    )

    smtp_user = os.environ.get(
        "SMTP_USER"
    )

    smtp_password = os.environ.get(
        "SMTP_PASSWORD"
    )

    smtp_from = os.environ.get(
        "SMTP_FROM",
        smtp_user,
    )

    # --------------------------------------------------------
    # Validate configuration
    # --------------------------------------------------------

    if not all(
        [
            smtp_host,
            smtp_user,
            smtp_password,
        ]
    ):

        raise RuntimeError(
            "Email is not configured. "
            "Set SMTP_HOST, SMTP_USER, and "
            "SMTP_PASSWORD in your .env file."
        )

    # --------------------------------------------------------
    # Create email
    # --------------------------------------------------------

    msg = MIMEMultipart()

    msg["From"] = smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.attach(
        MIMEText(
            body_text,
            "plain",
        )
    )

    # --------------------------------------------------------
    # Attach PDF
    # --------------------------------------------------------

    attachment = MIMEApplication(
        pdf_bytes,
        _subtype="pdf",
    )

    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=pdf_filename,
    )

    msg.attach(
        attachment
    )

    # --------------------------------------------------------
    # Connect to SMTP
    # --------------------------------------------------------

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
    ) as server:

        server.starttls()

        server.login(
            smtp_user,
            smtp_password,
        )

        server.send_message(
            msg
        )