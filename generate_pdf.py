# pdf_generator.py
from io import BytesIO
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor

def generate_pdf(content_text, mode="resume"):
    """
    Advanced ReportLab PDF Generator module configured for targeted executive sections.
    Explicitly breaks down Work Experience entries into structured Title, Company, 
    Years, and Work sub-elements.
    """
    buffer = BytesIO()
    
    # Page setup - Standard professional 0.75-inch margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    story = []
    lines = content_text.split('\n')
    
    # Target Section Headers
    TARGET_SECTIONS = [
        "CONTACT INFORMATION", 
        "PROFESSIONAL SUMMARY", 
        "SUMMARY",
        "WORK EXPERIENCE", 
        "PROFESSIONAL EXPERIENCE",
        "EXPERIENCE",
        "SKILLS", 
        "TECHNICAL SKILLS",
        "EDUCATION"
    ]
    
    # 1. Dynamic Name Extraction (Scans top 5 lines for the candidate's name)
    derived_title = "APPLICATION MATERIALS"
    for line in lines[:5]:
        cleaned = line.strip()
        if not cleaned:
            continue
        if '|' in cleaned:
            break
        if any(sec in cleaned.upper() for sec in TARGET_SECTIONS):
            break
        if not cleaned.startswith('#') and len(cleaned) < 50:
            derived_title = cleaned
            break

    # -------------------------------------------------------------------------
    # 2. Define High-End Palette & Segmented Typography Styles
    # -------------------------------------------------------------------------
    PRIMARY_COLOR = HexColor("#1E3A8A")   # Royal Slate Blue
    SECONDARY_COLOR = HexColor("#D97706")  # Warm Amber / Accent Gold
    TEXT_DARK = HexColor("#1F2937")        # Charcoal Body Text
    TEXT_MUTED = HexColor("#4B5563")       # Muted Contact Info
    
    title_style = ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=32,
        alignment=TA_CENTER,
        textColor=PRIMARY_COLOR,
        spaceAfter=6
    )
    
    meta_style = ParagraphStyle(
        name='DocMeta',
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        alignment=TA_CENTER,
        textColor=TEXT_MUTED,
        spaceAfter=14
    )
    
    heading_style = ParagraphStyle(
        name='SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=TA_LEFT,
        textColor=PRIMARY_COLOR,
        spaceBefore=4,
        spaceAfter=10,
        keepWithNext=True
    )
    
    # --- WORK EXPERIENCE METADATA SEGMENTS ---
    # Distinct Style for: Title & Years (Primary Line)
    title_line_style = ParagraphStyle(
        name='RoleTitleAndYears',
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        alignment=TA_LEFT,
        textColor=PRIMARY_COLOR,           # Accent color emphasizes the role title
        spaceBefore=8,
        spaceAfter=2,
        keepWithNext=True
    )
    
    # Distinct Style for: Company / Location Sub-headline
    company_style = ParagraphStyle(
        name='CompanySubHeadline',
        fontName='Helvetica-Oblique',       # Elegant italic styling distinguishes company
        fontSize=10.5,
        leading=14,
        alignment=TA_LEFT,
        textColor=TEXT_DARK,
        spaceBefore=0,
        spaceAfter=5,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        name='DocBody',
        fontName='Helvetica',
        fontSize=10.5 if mode == "cover_letter" else 10,
        leading=15 if mode == "cover_letter" else 14.5,
        alignment=TA_LEFT if mode == "cover_letter" else TA_JUSTIFY,
        textColor=TEXT_DARK,
        spaceAfter=10 if mode == "cover_letter" else 5
    )
    
    # Distinct Style for: Work accomplishments (Indented Bullet Block)
    bullet_style = ParagraphStyle(
        name='DocBullet',
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        textColor=TEXT_DARK,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    # -------------------------------------------------------------------------
    # 3. Parse & Build Document Flow
    # -------------------------------------------------------------------------
    story.append(Paragraph(derived_title.upper(), title_style))
    
    current_section = ""
    
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or cleaned_line == derived_title:
            continue
            
        # Clean HTML markup characters so ReportLab XML parser doesn't choke
        cleaned_line = (
            cleaned_line.replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')
        )
        
        # Translate standard markdown bold rules to inner HTML bold tags
        cleaned_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_line)
        
        # Track current section context to refine parser logic adjustments
        normalized_line = cleaned_line.lstrip('#').strip().upper()
        if any(sec == normalized_line or normalized_line.startswith(sec) for sec in TARGET_SECTIONS):
            current_section = next(sec for sec in TARGET_SECTIONS if sec == normalized_line or normalized_line.startswith(sec))
            
            if mode == "resume":
                story.append(HRFlowable(
                    width="100%", thickness=1.5, color=PRIMARY_COLOR,
                    spaceBefore=14, spaceAfter=6
                ))
            story.append(Paragraph(cleaned_line.lstrip('#').strip(), heading_style))
            continue

        # A. CATCH BULLET POINTS (Representing "Work" Accomplishments)
        if cleaned_line.startswith('- ') or cleaned_line.startswith('* ') or cleaned_line.startswith('• '):
            text = cleaned_line[2:].strip()
            bullet_text = f"<font color='{PRIMARY_COLOR.hexval()}'>&bull;</font> {text}"
            story.append(Paragraph(bullet_text, bullet_style))
            
        # B. CATCH RECURRING STRUCTURAL WORK EXPERIENCE LABELS
        elif mode == "resume" and ("WORK EXPERIENCE" in current_section or "EXPERIENCE" in current_section):
            # Check for common indicators of an entry containing Title, Company, or Years
            has_pipe = '|' in cleaned_line
            has_years = bool(re.search(r'(Present|\b20\d{2}\b)', cleaned_line))
            
            if has_pipe or has_years:
                # Tokenize line dynamically using common split patterns
                parts = [p.strip() for p in re.split(r'[\|\–\-–—]', cleaned_line) if p.strip()]
                
                # If we have distinct components, isolate Title, Company, and Years
                if len(parts) >= 2:
                    # Heuristic optimization: titles are often first or contain 'Director/Lead/Scientist/Engineer'
                    # Years are almost always at the end.
                    years_found = ""
                    remaining_parts = []
                    
                    for part in parts:
                        if re.search(r'(Present|\b20\d{2}\b)', part):
                            years_found = part.replace('<b>', '').replace('</b>', '')
                        else:
                            remaining_parts.append(part)
                    
                    if len(remaining_parts) >= 2:
                        title_text = remaining_parts[0]
                        company_text = remaining_parts[1]
                    elif len(remaining_parts) == 1:
                        title_text = remaining_parts[0]
                        company_text = "Organization"
                    else:
                        title_text = "Position"
                        company_text = "Organization"
                        
                    # Clean markdown markers off text fields safely
                    title_clean = title_text.replace('<b>', '').replace('</b>', '')
                    company_clean = company_text.replace('<b>', '').replace('</b>', '')
                    
                    # Construct Segment 1: Title and Years Right-Balanced via an elegant structural line
                    # Using a ReportLab inline spacing structure or clean template layout
                    role_html = f"<b>{title_clean}</b>"
                    if years_found:
                        role_html += f" &nbsp;|&nbsp; <font color='{SECONDARY_COLOR.hexval()}'>{years_found}</font>"
                    
                    story.append(Paragraph(role_html, title_line_style))
                    
                    # Construct Segment 2: Distinct Company Sub-Headline
                    story.append(Paragraph(company_clean, company_style))
                    
                else:
                    # Fallback structural presentation if line can't be tokenized accurately
                    story.append(Paragraph(cleaned_line, title_line_style))
            else:
                story.append(Paragraph(cleaned_line, body_style))
                
        # C. CATCH EVERYTHING ELSE (Contact metadata or Standard Paragraph Blocks)
        else:
            if '|' in cleaned_line:
                styled_meta = cleaned_line.replace('|', f" <font color='{SECONDARY_COLOR.hexval()}'>|</font> ")
                story.append(Paragraph(styled_meta, meta_style))
            else:
                story.append(Paragraph(cleaned_line, body_style))
                
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
