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
    Advanced ReportLab PDF Generator module configured for targeted executive sections:
    Contact Information, Professional Summary, Work Experience, Skills, and Education.
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
    
    # -------------------------------------------------------------------------
    # 1. Target Resume Section Headings Definitions
    # -------------------------------------------------------------------------
    TARGET_SECTIONS = [
       # "CONTACT INFORMATION", 
        "PROFESSIONAL SUMMARY", 
        "SUMMARY",
        "WORK EXPERIENCE", 
        "PROFESSIONAL EXPERIENCE",
        "SKILLS", 
        "TECHNICAL SKILLS",
        "EDUCATION"
    ]
    
    # 2. Dynamic Name Extraction (Scans top 5 lines for the candidate's name)
    derived_title = "APPLICATION MATERIALS"
    for line in lines[:5]:
        cleaned = line.strip()
        if not cleaned:
            continue
        if '|' in cleaned:
            break
        # If the top line is already explicitly labeled as contact info, skip it for the big title
        if any(sec in cleaned.upper() for sec in TARGET_SECTIONS):
            break
        if not cleaned.startswith('#') and len(cleaned) < 50:
            derived_title = cleaned
            break

    # -------------------------------------------------------------------------
    # 3. Define Palette & Enhanced Typography
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
        fontSize=18,                       # Big bold 18pt section headers
        leading=22,
        alignment=TA_LEFT,
        textColor=PRIMARY_COLOR,
        spaceBefore=4,
        spaceAfter=10,
        keepWithNext=True
    )
    
    job_title_style = ParagraphStyle(
        name='JobTitle',
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        alignment=TA_LEFT,
        textColor=TEXT_DARK,
        spaceBefore=8,
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
    # 4. Parse & Build Document Flow
    # -------------------------------------------------------------------------
    # Render main Candidate Name Header at the absolute top
    story.append(Paragraph(derived_title.upper(), title_style))
    
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or cleaned_line == derived_title:
            continue
            
        # Clean HTML characters so ReportLab's inner XML engine doesn't crash
        cleaned_line = (
            cleaned_line.replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')
        )
        
        # Translate markdown bold rules into native FPDF inline markup tags
        cleaned_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_line)
        
        # Normalize the string to see if it qualifies as one of our target resume sections
        normalized_line = cleaned_line.lstrip('#').strip().upper()
        is_target_section = any(sec == normalized_line or normalized_line.startswith(sec) for sec in TARGET_SECTIONS)
        
        # A. Catch Major Targeted Sections
        if cleaned_line.startswith('#') or is_target_section:
            text = cleaned_line.lstrip('#').strip()
            
            # Draw strong structural lines between sections for resume layouts
            if mode == "resume":
                story.append(HRFlowable(
                    width="100%", thickness=1.5, color=PRIMARY_COLOR,
                    spaceBefore=14, spaceAfter=6
                ))
            story.append(Paragraph(text, heading_style))
            
        # B. Catch Bullet Points
        elif cleaned_line.startswith('- ') or cleaned_line.startswith('* ') or cleaned_line.startswith('• '):
            text = cleaned_line[2:].strip()
            bullet_text = f"<font color='{PRIMARY_COLOR.hexval()}'>&bull;</font> {text}"
            story.append(Paragraph(bullet_text, bullet_style))
            
        # C. Catch Normal Text / Inline Elements
        else:
            # Format Contact Information cleanly if a pipe divider line exists
            if '|' in cleaned_line:
                styled_meta = cleaned_line.replace('|', f" <font color='{SECONDARY_COLOR.hexval()}'>|</font> ")
                story.append(Paragraph(styled_meta, meta_style))
            
            # Format job titles / timeline headings inside Work Experience cleanly
            elif mode == "resume" and (cleaned_line.startswith('<b>') or any(token in cleaned_line for token in ["Present", "202", "201"])):
                story.append(Paragraph(cleaned_line, job_title_style))
                
            else:
                story.append(Paragraph(cleaned_line, body_style))
                
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
