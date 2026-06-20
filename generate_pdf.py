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
    Safely leaves formal letter greetings (e.g., 'DEAR HIRING TEAM') as native body text.
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
        # "EXPERIENCE",
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
    
    title_line_style = ParagraphStyle(
        name='RoleTitleAndYears',
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        alignment=TA_LEFT,
        textColor=PRIMARY_COLOR,
        spaceBefore=8,
        spaceAfter=2,
        keepWithNext=True
    )
    
    company_style = ParagraphStyle(
        name='CompanySubHeadline',
        fontName='Helvetica-Oblique',
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
    if mode == "resume":
        story.append(Paragraph(derived_title.upper(), title_style))
    
    current_section = ""
    
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
            
        if mode == "resume" and cleaned_line == derived_title:
            continue
            
        # Clean HTML markup characters so ReportLab XML parser doesn't crash
        cleaned_line = (
            cleaned_line.replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')
        )
        
        # Translate standard markdown bold rules to inner HTML bold tags
        cleaned_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_line)
        
        # Normalize the line to check against targeted structural headers
        normalized_line = cleaned_line.lstrip('#').strip().upper()
        
        # Explicit exception rule: Ignore lines that start with standard greetings (e.g. DEAR...)
        is_greeting = normalized_line.startswith("DEAR ") or normalized_line.startswith("TO WHOM")
        
        is_target_section = (
            not is_greeting and 
            any(sec == normalized_line or normalized_line.startswith(sec) for sec in TARGET_SECTIONS)
        )
        
        # A. CATCH MAJOR TARGETED HEADINGS (With greeting protection enabled)
        if (cleaned_line.startswith('#') and not is_greeting) or is_target_section:
            current_section = next((sec for sec in TARGET_SECTIONS if sec == normalized_line or normalized_line.startswith(sec)), "")
            
            if mode == "resume":
                story.append(HRFlowable(
                    width="100%", thickness=1.5, color=PRIMARY_COLOR,
                    spaceBefore=14, spaceAfter=6
                ))
            story.append(Paragraph(cleaned_line.lstrip('#').strip(), heading_style))
            continue

        # B. CATCH BULLET POINTS
        if cleaned_line.startswith('- ') or cleaned_line.startswith('* ') or cleaned_line.startswith('• '):
            text = cleaned_line[2:].strip()
            bullet_text = f"<font color='{PRIMARY_COLOR.hexval()}'>&bull;</font> {text}"
            story.append(Paragraph(bullet_text, bullet_style))
            
        # C. CATCH RECURRING STRUCTURAL WORK EXPERIENCE LABELS (Resume Mode Only)
        elif mode == "resume" and ("WORK EXPERIENCE" in current_section or "EXPERIENCE" in current_section):
            has_pipe = '|' in cleaned_line
            has_years = bool(re.search(r'(Present|\b20\d{2}\b)', cleaned_line))
            
            if has_pipe or has_years:
                parts = [p.strip() for p in re.split(r'[\|\–\-–—]', cleaned_line) if p.strip()]
                
                if len(parts) >= 2:
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
                    else:
                        title_text = remaining_parts[0] if remaining_parts else "Position"
                        company_text = "Organization"
                        
                    title_clean = title_text.replace('<b>', '').replace('</b>', '')
                    company_clean = company_text.replace('<b>', '').replace('</b>', '')
                    
                    role_html = f"<b>{title_clean}</b>"
                    if years_found:
                        role_html += f" &nbsp;|&nbsp; <font color='{SECONDARY_COLOR.hexval()}'>{years_found}</font>"
                    
                    story.append(Paragraph(role_html, title_line_style))
                    story.append(Paragraph(company_clean, company_style))
                else:
                    story.append(Paragraph(cleaned_line, title_line_style))
            else:
                story.append(Paragraph(cleaned_line, body_style))
                
        # D. CATCH EVERYTHING ELSE (Greetings fall perfectly down here)
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
