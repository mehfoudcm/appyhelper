# pdf_generator.py
from io import BytesIO
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor

def generate_pdf(content_text, mode="resume"):
    """
    Advanced ReportLab PDF Generator module configured for targeted executive sections.
    Applies independent subheader fonts to parsed metadata targets without showing labels.
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
        # "PROFESSIONAL EXPERIENCE",
        # "EXPERIENCE",
        "SKILLS", 
        "TECHNICAL SKILLS",
        "EDUCATION"
    ]
    
    # Dynamic Name Extraction (Scans top 5 lines for the candidate's name)
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
    # Typography & Subheader Palette Design
    # -------------------------------------------------------------------------
    PRIMARY_COLOR = HexColor("#1E3A8A")   # Royal Slate Blue
    SECONDARY_COLOR = HexColor("#D97706")  # Warm Amber
    TEXT_DARK = HexColor("#1F2937")        # Charcoal
    TEXT_MUTED = HexColor("#4B5563")       # Slate Gray
    
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
    
    # Font Style 1: "Experience" Section Heading
    heading_style = ParagraphStyle(
        name='SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=TA_LEFT,
        textColor=PRIMARY_COLOR,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    
    # Font Style 2: "Title" (Role Headline)
    role_title_style = ParagraphStyle(
        name='SubTitleRole',
        fontName='Helvetica-Bold',         # Solid Bold
        fontSize=12,
        leading=16,
        alignment=TA_LEFT,
        textColor=PRIMARY_COLOR,
        spaceBefore=6,
        spaceAfter=1,
        keepWithNext=True
    )
    
    # Font Style 3: "Company Name" Subheader
    company_name_style = ParagraphStyle(
        name='SubCompany',
        fontName='Helvetica-BoldOblique',   # Distinct Bold Italic styling
        fontSize=10.5,
        leading=14,
        alignment=TA_LEFT,
        textColor=TEXT_DARK,
        spaceBefore=1,
        spaceAfter=1,
        keepWithNext=True
    )
    
    # Font Style 4: "Years" Subheader
    years_style = ParagraphStyle(
        name='SubYears',
        fontName='Helvetica-Oblique',       # Clean structural Italic layout
        fontSize=9.5,
        leading=13,
        alignment=TA_LEFT,
        textColor=SECONDARY_COLOR,
        spaceBefore=0,
        spaceAfter=4,
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
    # Parse & Build Document Flow
    # -------------------------------------------------------------------------
    if mode == "resume":
        story.append(Paragraph(derived_title.upper(), title_style))
    
    current_section = ""
    
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
            
        if mode == "resume" and cleaned_line == derived_title:
            continue
            
        cleaned_line = (
            cleaned_line.replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')
        )
        cleaned_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_line)
        
        normalized_line = cleaned_line.lstrip('#').strip().upper()
        is_greeting = normalized_line.startswith("DEAR ") or normalized_line.startswith("TO WHOM")
        
        is_target_section = (
            not is_greeting and 
            any(sec == normalized_line or normalized_line.startswith(sec) for sec in TARGET_SECTIONS)
        )
        
        # A. EXPERIENCE SECTION HEADINGS
        if (cleaned_line.startswith('#') and not is_greeting) or is_target_section:
            current_section = next((sec for sec in TARGET_SECTIONS if sec == normalized_line or normalized_line.startswith(sec)), "")
            
            if mode == "resume":
                story.append(HRFlowable(
                    width="100%", thickness=1.5, color=PRIMARY_COLOR,
                    spaceBefore=12, spaceAfter=6
                ))
            story.append(Paragraph(cleaned_line.lstrip('#').strip(), heading_style))
            continue

        # B. WORK ACCOMPLISHMENT BULLETS
        if cleaned_line.startswith('- ') or cleaned_line.startswith('* ') or cleaned_line.startswith('• '):
            text = cleaned_line[2:].strip()
            bullet_text = f"<font color='{PRIMARY_COLOR.hexval()}'>&bull;</font> {text}"
            story.append(Paragraph(bullet_text, bullet_style))
            
        # C. GRANULAR WORK EXPERIENCE METADATA PARSING
        elif mode == "resume" and ("WORK EXPERIENCE" in current_section or "EXPERIENCE" in current_section):
            # Check if this line is explicitly stating a field or structured via standard pipes
            lower_line = cleaned_line.lower()
            
            # Pattern 1: Explicit labels present (e.g., "Company: Acme Corp")
            if "company:" in lower_line or "title:" in lower_line or "years:" in lower_line:
                # Strip out the actual label words cleanly via regex
                clean_text = re.sub(r'(?i)\b(company|title|years|duration|date|dates)\s*:\s*', '', cleaned_line)
                clean_text = clean_text.replace('<b>', '').replace('</b>', '').strip()
                
                if "title:" in lower_line:
                    story.append(Paragraph(clean_text, role_title_style))
                elif "company:" in lower_line:
                    story.append(Paragraph(clean_text, company_name_style))
                elif "years:" in lower_line:
                    story.append(Paragraph(clean_text, years_style))
                    
            # Pattern 2: Inline layout fallback (e.g., "Senior Engineer | Google | 2022 - Present")
            elif '|' in cleaned_line or bool(re.search(r'(Present|\b20\d{2}\b)', cleaned_line)):
                parts = [p.strip().replace('<b>', '').replace('</b>', '') for p in re.split(r'[\|\–\-–—]', cleaned_line) if p.strip()]
                
                # Dynamically assign cascading subheaders sequentially down the layout tree
                if len(parts) >= 3:
                    story.append(Paragraph(parts[0], role_title_style))       # Title
                    story.append(Paragraph(parts[1], company_name_style))   # Company Name
                    story.append(Paragraph(parts[2], years_style))          # Years
                elif len(parts) == 2:
                    story.append(Paragraph(parts[0], role_title_style))       # Title
                    story.append(Paragraph(parts[1], company_name_style))   # Company Name
                else:
                    story.append(Paragraph(cleaned_line, role_title_style))
            else:
                story.append(Paragraph(cleaned_line, body_style))
                
        # D. STANDALONE PARAGRAPHS & CONTACT META
        else:
            if '|' in cleaned_line:
                if mode == "resume":
                    styled_meta = cleaned_line.replace('|', f" <font color='{SECONDARY_COLOR.hexval()}'>|</font> ")
                    story.append(Paragraph(styled_meta, meta_style))
                else:
                    story.append(Paragraph(cleaned_line, body_style))
            else:
                story.append(Paragraph(cleaned_line, body_style))
                
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
