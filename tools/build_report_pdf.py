from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from svglib.svglib import svg2rlg


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "PROJECT_REPORT.md"
OUTPUT = ROOT / "output" / "pdf" / "RCIA_Project_Report.pdf"
PAGE_W, PAGE_H = A4

NAVY = colors.HexColor("#0B1F3A")
BLUE = colors.HexColor("#1D4ED8")
CYAN = colors.HexColor("#06B6D4")
INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#5D6B82")
PALE = colors.HexColor("#F2F6FC")
LINE = colors.HexColor("#D7E0EC")


def clean(value: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2022": "-",
        "\u2192": "->",
        "\u00d7": "x",
        "\u2264": "<=",
        "\u2265": ">=",
        "\u2011": "-",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def inline_markup(value: str) -> str:
    value = clean(value)
    value = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"\[([^]]+)\]\(([^)]+)\)", r"\1", value)
    value = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"__([^_]+)__", r"<b>\1</b>", value)
    return value


class CoverPage(Flowable):
    def __init__(self) -> None:
        super().__init__()
        self.width = PAGE_W - 36 * mm
        self.height = PAGE_H - 36 * mm

    def wrap(self, avail_width, avail_height):
        return avail_width, avail_height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(-18 * mm, -18 * mm, PAGE_W, PAGE_H, fill=1, stroke=0)
        canvas.setFillColor(CYAN)
        canvas.circle(PAGE_W - 40 * mm, PAGE_H - 40 * mm, 38 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.Color(1, 1, 1, alpha=0.08))
        canvas.circle(PAGE_W - 40 * mm, PAGE_H - 40 * mm, 25 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 30)
        canvas.drawString(20 * mm, PAGE_H - 72 * mm, "Requirement Change")
        canvas.drawString(20 * mm, PAGE_H - 86 * mm, "Impact Analyzer")
        canvas.setFillColor(colors.HexColor("#B9D9FF"))
        canvas.setFont("Helvetica", 14)
        canvas.drawString(20 * mm, PAGE_H - 104 * mm, "RCIA - Complete Project Report")
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica", 11)
        canvas.drawString(20 * mm, 50 * mm, "AI-assisted requirement analysis with transparent evidence")
        canvas.setFillColor(colors.HexColor("#B9D9FF"))
        canvas.setFont("Helvetica", 10)
        canvas.drawString(20 * mm, 39 * mm, "Live demo: https://rcia.onrender.com/")
        canvas.drawString(20 * mm, 31 * mm, "Source: github.com/shridhar07122004/RCIA")
        canvas.drawRightString(PAGE_W - 20 * mm, 22 * mm, f"Generated {date.today().isoformat()}")
        canvas.restoreState()


class SVGFlowable(Flowable):
    def __init__(self, path: Path, max_width: float, max_height: float = 145 * mm):
        super().__init__()
        self.path = path
        self.drawing = svg2rlg(str(path))
        if self.drawing is None:
            raise ValueError(f"Unable to read SVG: {path}")
        scale = min(max_width / self.drawing.width, max_height / self.drawing.height)
        self.scale = min(scale, 1.0)
        self.width = self.drawing.width * self.scale
        self.height = self.drawing.height * self.scale

    def wrap(self, avail_width, avail_height):
        return min(self.width, avail_width), self.height

    def draw(self):
        self.canv.saveState()
        self.canv.translate(0, 0)
        self.canv.scale(self.scale, self.scale)
        self.drawing.drawOn(self.canv, 0, 0)
        self.canv.restoreState()


def styles():
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "Body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.4,
            leading=13.5, textColor=INK, spaceAfter=5, alignment=TA_LEFT,
        ),
        "h1": ParagraphStyle(
            "H1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=18,
            leading=22, textColor=NAVY, spaceBefore=12, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=12.5,
            leading=16, textColor=BLUE, spaceBefore=9, spaceAfter=5,
        ),
        "h3": ParagraphStyle(
            "H3", parent=base["Heading3"], fontName="Helvetica-Bold", fontSize=10.5,
            leading=14, textColor=CYAN, spaceBefore=7, spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "Small", parent=base["BodyText"], fontName="Helvetica", fontSize=8,
            leading=10.5, textColor=MUTED, spaceAfter=4,
        ),
        "caption": ParagraphStyle(
            "Caption", parent=base["BodyText"], fontName="Helvetica-Oblique", fontSize=8,
            leading=10, textColor=MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=9,
        ),
        "code": ParagraphStyle(
            "Code", parent=base["Code"], fontName="Courier", fontSize=7.2,
            leading=9, textColor=INK, backColor=PALE, borderColor=LINE,
            borderWidth=0.5, borderPadding=6, spaceBefore=4, spaceAfter=7,
        ),
    }


def table_flowable(rows, width):
    if not rows:
        return None
    formatted = []
    for row_index, row in enumerate(rows):
        formatted.append([
            Paragraph(inline_markup(cell.strip()), ParagraphStyle(
                f"Cell{row_index}", fontName="Helvetica-Bold" if row_index == 0 else "Helvetica",
                fontSize=7.6, leading=9.3, textColor=colors.white if row_index == 0 else INK,
            )) for cell in row
        ])
    columns = max(len(row) for row in rows)
    col_width = width / columns
    table = Table(formatted, colWidths=[col_width] * columns, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def add_page_chrome(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(18 * mm, PAGE_H - 15 * mm, PAGE_W - 18 * mm, PAGE_H - 15 * mm)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(NAVY)
        canvas.drawString(18 * mm, PAGE_H - 11 * mm, "RCIA | PROJECT REPORT")
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(PAGE_W - 18 * mm, 11 * mm, f"Page {doc.page}")
        canvas.line(18 * mm, 15 * mm, PAGE_W - 18 * mm, 15 * mm)
    canvas.restoreState()


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    report = SOURCE.read_text(encoding="utf-8")
    lines = report.splitlines()
    s = styles()
    usable_width = PAGE_W - 36 * mm
    story = [CoverPage(), PageBreak()]

    # A compact contents page makes the report easy to navigate in a PDF viewer.
    story += [Paragraph("Contents", s["h1"]), Spacer(1, 2 * mm)]
    contents = []
    for line in lines:
        match = re.match(r"^## (\d+)\. (.+)$", line)
        if match:
            contents.append([match.group(1), clean(match.group(2))])
    contents_table = Table(
        [[Paragraph("Section", s["small"]), Paragraph("Topic", s["small"])]
         ] + [[Paragraph(number, s["body"]), Paragraph(topic, s["body"])] for number, topic in contents],
        colWidths=[20 * mm, usable_width - 20 * mm],
    )
    contents_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story += [contents_table, PageBreak()]

    i = 0
    paragraph_lines = []
    code_lines = []
    in_code = False

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(line.strip() for line in paragraph_lines).strip()
            if text:
                story.append(Paragraph(inline_markup(text), s["body"]))
            paragraph_lines = []

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(Preformatted(clean("\n".join(code_lines)), s["code"]))
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if not line.strip():
            flush_paragraph()
            i += 1
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            title = inline_markup(heading.group(2))
            if level == 2 and clean(heading.group(2)).startswith("15. Screenshots"):
                story.append(PageBreak())
            if level == 1:
                story.append(Paragraph(title, s["h1"]))
            elif level == 2:
                story.append(Paragraph(title, s["h2"]))
            else:
                story.append(Paragraph(title, s["h3"]))
            i += 1
            continue

        if re.match(r"^\|.*\|$", line):
            flush_paragraph()
            table_rows = []
            while i < len(lines) and re.match(r"^\|.*\|$", lines[i].strip()):
                cells = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
                    table_rows.append(cells)
                i += 1
            table = table_flowable(table_rows, usable_width)
            if table:
                story.append(table)
                story.append(Spacer(1, 4 * mm))
            continue

        image_match = re.match(r"!\[([^]]*)\]\(([^)]+)\)", line)
        if image_match:
            flush_paragraph()
            image_path = ROOT / image_match.group(2).replace("/", "\\")
            if image_path.exists():
                story.append(KeepTogether([
                    SVGFlowable(image_path, usable_width, max_height=125 * mm),
                    Paragraph(clean(image_match.group(1)), s["caption"]),
                ]))
                story.append(PageBreak())
            i += 1
            continue

        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if bullet:
            flush_paragraph()
            story.append(Paragraph(inline_markup(bullet.group(1)), ParagraphStyle(
                "Bullet", parent=s["body"], leftIndent=12, firstLineIndent=-8,
                bulletIndent=0, bulletText="-",
            )))
            i += 1
            continue

        paragraph_lines.append(line)
        i += 1

    flush_paragraph()
    doc = SimpleDocTemplate(
        str(OUTPUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=22 * mm, bottomMargin=20 * mm, title="RCIA Complete Project Report",
        author="Requirement Change Impact Analyzer",
    )
    doc.build(story, onFirstPage=add_page_chrome, onLaterPages=add_page_chrome)
    print(OUTPUT)


if __name__ == "__main__":
    build()
