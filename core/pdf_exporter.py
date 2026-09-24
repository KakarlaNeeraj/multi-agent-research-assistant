import io
import re
import html
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header
        if self._pageNumber > 1:
            self.drawString(54, 11 * 72 - 36, "Autonomous Research Report | Multi-Agent Assistant")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 40, 8.5 * 72 - 54, 11 * 72 - 40)
            
        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 36, footer_text)
        self.drawString(54, 36, "Generated with Verified Source Provenance")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 46, 8.5 * 72 - 54, 46)
        
        self.restoreState()


def clean_markdown_to_xml(text: str) -> str:
    """
    Safely escapes XML special characters while converting markdown bold/italic/links
    into valid ReportLab XML tags without tag overlap issues.
    """
    # 1. Escape ampersands and xml symbols first
    text = html.escape(text)

    # 2. Convert markdown bold **text** to <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    
    # 3. Convert markdown italic *text* or _text_ to <i>text</i>
    text = re.sub(r'(?<!\*)\*([^\*]+?)\*(?!\*)', r'<i>\1</i>', text)
    
    # 4. Convert inline code `text` to font
    text = re.sub(r'`([^`]+?)`', r'<font face="Courier">\1</font>', text)

    # 5. Clean up markdown links [title](url) safely without broken tags
    # Replace [Title](url) with Title (url) or safe link
    def replace_link(match):
        title = match.group(1)
        url = match.group(2)
        return f'<u>{title}</u> (<font color="#2563EB">{url}</font>)'
        
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)

    return text


def markdown_to_pdf_bytes(markdown_text: str, topic: str = "Research Report") -> bytes:
    """
    Converts markdown research report into robust PDF bytes.
    Includes bulletproof fallback against XML/HTML parsing errors.
    """
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=8
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#2563EB"),
        spaceBefore=12,
        spaceAfter=5
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=8,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=body_style,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor("#475569"),
        leftIndent=10,
        spaceBefore=3,
        spaceAfter=5
    )

    story = []
    
    lines = markdown_text.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped:
            story.append(Spacer(1, 3))
            continue
            
        try:
            if stripped.startswith('# '):
                safe_txt = html.escape(stripped[2:])
                story.append(Paragraph(safe_txt, title_style))
                story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB"), spaceBefore=3, spaceAfter=8))
            elif stripped.startswith('## '):
                safe_txt = html.escape(stripped[3:])
                story.append(Paragraph(safe_txt, h1_style))
            elif stripped.startswith('### '):
                safe_txt = html.escape(stripped[4:])
                story.append(Paragraph(safe_txt, h2_style))
            elif stripped.startswith('> '):
                safe_txt = clean_markdown_to_xml(stripped[2:])
                story.append(Paragraph(safe_txt, callout_style))
            elif stripped.startswith('- ') or stripped.startswith('* '):
                safe_txt = clean_markdown_to_xml(stripped[2:])
                story.append(Paragraph(f"• {safe_txt}", bullet_style))
            elif re.match(r'^\d+\.\s', stripped):
                match = re.match(r'^(\d+\.)\s+(.*)$', stripped)
                num = match.group(1)
                safe_txt = clean_markdown_to_xml(match.group(2))
                story.append(Paragraph(f"<b>{num}</b> {safe_txt}", bullet_style))
            else:
                safe_txt = clean_markdown_to_xml(stripped)
                story.append(Paragraph(safe_txt, body_style))
        except Exception:
            # Absolute bulletproof fallback: plain escaped text without XML markup
            plain_escaped = html.escape(stripped)
            story.append(Paragraph(plain_escaped, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()
