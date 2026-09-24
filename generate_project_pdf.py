"""
Script to generate a professional PDF document explaining the Multi-Agent Research Assistant project.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (Skip on first page)
        if self._pageNumber > 1:
            self.drawString(54, 11 * 72 - 36, "Multi-Agent Research Assistant | AI/ML Project Documentation")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 11 * 72 - 42, 8.5 * 72 - 54, 11 * 72 - 42)
            
        # Footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 54, 36, footer_text)
        self.drawString(54, 36, "CONFIDENTIAL & PROPRIETARY — AI/ML ENGINEERING PORTFOLIO")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 8.5 * 72 - 54, 48)
        
        self.restoreState()


def create_project_pdf(output_filename="MultiAgent_Research_Assistant_Project_Guide.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1E293B")
    accent_color = colors.HexColor("#2563EB")
    secondary_accent = colors.HexColor("#0D9488")
    text_dark = colors.HexColor("#0F172A")
    text_muted = colors.HexColor("#475569")
    bg_light = colors.HexColor("#F8FAFC")
    border_color = colors.HexColor("#CBD5E1")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=text_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_dark,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=4,
        spaceAfter=4
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E3A8A"),
        spaceBefore=4,
        spaceAfter=4
    )

    story = []

    # Title & Metadata
    story.append(Paragraph("Multi-Agent Research Assistant", title_style))
    story.append(Paragraph("Autonomous Multi-Agent Planning, Web Search, Fact Synthesis & Cited Report Generation (Streamlit + Pure Python)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceBefore=2, spaceAfter=12))

    # Meta banner table
    meta_data = [
        [
            Paragraph("<b>Target Role:</b> AI / ML Engineer", body_style),
            Paragraph("<b>Stack:</b> Python, Streamlit, Local LLM (Ollama/LMStudio), Tavily/DDG", body_style),
        ],
        [
            Paragraph("<b>Deployment:</b> Streamlit Cloud / HuggingFace Spaces", body_style),
            Paragraph("<b>Architecture:</b> Planner-Researcher-Writer Agent Swarm", body_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_light),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Section 1: Project Overview & Motivation
    story.append(Paragraph("1. Project Executive Summary & Motivation", h1_style))
    story.append(Paragraph(
        "Standard Large Language Models (LLMs) suffer from two core limitations when generating in-depth research: "
        "<b>knowledge cutoff</b> (inability to fetch live information) and <b>hallucinations</b> (inventing facts or fake references). "
        "Single-prompt RAG architectures struggle with multi-hop reasoning and broad topic synthesis.",
        body_style
    ))
    story.append(Paragraph(
        "This project implements an autonomous <b>Multi-Agent Research Assistant</b> that deconstructs complex queries, "
        "executes parallel live web searches with deterministic citation tracking, and synthesizes an academic-grade report with verified inline citations. "
        "Built strictly in <b>Pure Python and Streamlit</b>, it eliminates full-stack complexity while delivering an interactive, production-grade interface.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Section 2: Multi-Agent System Architecture
    story.append(Paragraph("2. Multi-Agent System Architecture", h1_style))
    story.append(Paragraph(
        "The system relies on a directed state graph containing three specialized agent roles plus an automated quality critic node:",
        body_style
    ))

    # Agents Table
    agents_data = [
        [Paragraph("<b>Agent Role</b>", body_style), Paragraph("<b>Core Responsibilities</b>", body_style), Paragraph("<b>Input / Output Artifacts</b>", body_style)],
        [
            Paragraph("<b>1. Planner Agent</b>", body_style),
            Paragraph("• Deconstructs ambiguous topics into logical research sub-tasks.<br/>• Formulates targeted, diverse search queries for each sub-topic.<br/>• Constructs a structured table of contents.", body_style),
            Paragraph("<b>In:</b> User prompt, depth setting<br/><b>Out:</b> JSON <code>ResearchPlan</code>", body_style)
        ],
        [
            Paragraph("<b>2. Search / Research Agent</b>", body_style),
            Paragraph("• Executes search queries asynchronously via Tavily / DuckDuckGo.<br/>• Extracts clean page text, filters noise, deduplicates content.<br/>• Maps each factual excerpt to its canonical URL index <code>[1]</code>, <code>[2]</code>.", body_style),
            Paragraph("<b>In:</b> Search queries list<br/><b>Out:</b> List of <code>EvidenceItem</code> + URL bibliography", body_style)
        ],
        [
            Paragraph("<b>3. Writer / Synthesizer Agent</b>", body_style),
            Paragraph("• Synthesizes multi-source evidence into a cohesive markdown document.<br/>• Enforces strict grounding with inline numerical citations.<br/>• Generates Executive Summary, Detailed Sections, Key Takeaways, and Bibliography.", body_style),
            Paragraph("<b>In:</b> Plan + Evidence items<br/><b>Out:</b> Formatted Markdown research report", body_style)
        ],
        [
            Paragraph("<b>4. Critic / Fact-Checker (Node)</b>", body_style),
            Paragraph("• Validates that all factual claims map to indexed citations.<br/>• Detects missing citations or logical gaps.<br/>• Either approves for export or triggers a corrective search sub-loop.", body_style),
            Paragraph("<b>In:</b> Draft report + Evidence<br/><b>Out:</b> Approved Report / Refinement directives", body_style)
        ]
    ]
    agents_table = Table(agents_data, colWidths=[110, 240, 154])
    agents_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(agents_table)
    story.append(Spacer(1, 14))

    # Section 3: Data Flow & State Management
    story.append(Paragraph("3. Shared State Schema (Pydantic / TypedDict)", h1_style))
    story.append(Paragraph(
        "Communication between agents is strictly controlled through an immutable state object passed across nodes:",
        body_style
    ))

    code_snippet = """class ResearchState(TypedDict):
    topic: str                     # User query
    report_type: str               # Academic | Technical | Executive Brief
    plan: ResearchPlan             # Outline + list of search sub-queries
    evidence: List[EvidenceItem]   # Web snippets, source URLs, timestamps
    citations: Dict[int, Source]   # Numbered source index ([1] -> URL/Title)
    draft_report: str              # Draft synthesized markdown
    final_report: str              # Verified cited report
    logs: List[str]                # Real-time event log for Streamlit UI"""

    code_table = Table([[Paragraph(f"<pre>{code_snippet.replace(' ', '&nbsp;').replace(chr(10), '<br/>')}</pre>", code_style)]], colWidths=[504])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#1E293B")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0F172A")),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    # For dark background, text needs to be light
    code_style.textColor = colors.HexColor("#F8FAFC")
    code_table_styled = Table([[Paragraph(f"<font color='#F8FAFC'>{code_snippet.replace(' ', '&nbsp;').replace(chr(10), '<br/>')}</font>", code_style)]], colWidths=[504])
    code_table_styled.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#1E293B")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0F172A")),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(code_table_styled)
    story.append(Spacer(1, 14))

    # Section 4: Streamlit UI & User Experience
    story.append(Paragraph("4. Streamlit Interactive Interface (No Full-Stack Overhead)", h1_style))
    story.append(Paragraph(
        "Streamlit allows pure Python developers to create rich, reactive interfaces with live agent feedback:",
        body_style
    ))
    story.append(Paragraph("• <b>Control Sidebar:</b> Select Model (OpenAI GPT-4o, Claude 3.5, Gemini 1.5/2.0, Ollama), search depth (Quick vs. Deep), and tone format.", bullet_style))
    story.append(Paragraph("• <b>Live Multi-Agent Accordions:</b> Expander panels that open in real time showing the Planner's outline, Searcher's visited URLs, and Critic's evaluation.", bullet_style))
    story.append(Paragraph("• <b>Live Markdown Preview:</b> Beautiful rendered report with clickable source hyperlinks.", bullet_style))
    story.append(Paragraph("• <b>One-Click Export:</b> Instant download buttons for PDF, Markdown (.md), and JSON state dumps.", bullet_style))
    story.append(Spacer(1, 12))

    # Section 5: AI/ML Engineering Core Concepts Tested
    story.append(Paragraph("5. Key AIML Competencies Demonstrated", h1_style))
    story.append(Paragraph("• <b>Agentic Decomposition:</b> Preventing single-prompt context collapse by breaking macro goals into specialized sub-agents.", bullet_style))
    story.append(Paragraph("• <b>Grounding & Provenance:</b> Enforcing strict numerical citation schemas to eliminate hallucination in domain-critical research.", bullet_style))
    story.append(Paragraph("• <b>Tool Calling & Structured Parsing:</b> Using Pydantic output parsers and native function calling for deterministic state transitions.", bullet_style))
    story.append(Paragraph("• <b>Cost & Latency Optimization:</b> Parallel query execution and targeted context slicing to keep token usage minimal.", bullet_style))
    story.append(Spacer(1, 14))

    # Section 6: Interview & Project Defense Guide
    story.append(Paragraph("6. Project Explanation / Interview Defense Cheatsheet", h1_style))
    
    qna_data = [
        [
            Paragraph("<b>Typical Question</b>", body_style),
            Paragraph("<b>Recommended Technical Answer</b>", body_style)
        ],
        [
            Paragraph("<i>Why multi-agent instead of a simple RAG pipeline?</i>", body_style),
            Paragraph("Standard RAG is passive (retrieves chunks for 1 query). Complex topics require multi-angle query expansion, iterative gap filling, and separated synthesis phases to produce coherent, long-form structured reports.", body_style)
        ],
        [
            Paragraph("<i>How do you prevent citation hallucination?</i>", body_style),
            Paragraph("The Search Agent assigns unique integer IDs to raw sources before synthesis. The Writer prompt explicitly limits citations to the provided index dictionary, and the Critic node validates all regex <code>\\[\\d+\\]</code> tags against the index.", body_style)
        ],
        [
            Paragraph("<i>Why pure Python / Streamlit?</i>", body_style),
            Paragraph("Enables fast iteration on AI algorithms, agent topologies, and prompt strategies without spending 70% of engineering bandwidth on frontend state/bundling. Perfect for ML production prototypes and internal enterprise tooling.", body_style)
        ]
    ]
    qna_table = Table(qna_data, colWidths=[150, 354])
    qna_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E2E8F0")),
        ('BOX', (0,0), (-1,-1), 1, border_color),
        ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(qna_table)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully created: {output_filename}")

if __name__ == "__main__":
    create_project_pdf("/Users/tharunkakarla/Multi-agent research assiant/MultiAgent_Research_Assistant_Project_Guide.pdf")
