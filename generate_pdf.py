from io import BytesIO
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor

def generate_pdf(content_text, mode="resume"):
    """
    Advanced ReportLab PDF Generator.
    
    Parameters:
    - content_text (str): The markdown text to convert.
    - mode (str): 'resume' or 'cover_letter'. Adjusts spacing, rules, and text justification.
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
    # 1. Dynamic Name Extraction (Scans top 5 lines for the name)
    # -------------------------------------------------------------------------
    derived_title = "APPLICATION MATERIALS"
    
    for line in lines[:5]:
        cleaned = line.strip()
        if not cleaned:
            continue
        if '|' in cleaned:
            break
        if not cleaned.startswith('#') and len(cleaned) < 50:
            derived_title = cleaned
            break

    # -------------------------------------------------------------------------
    # 2. Define Palette & Enhanced Typography
    # -------------------------------------------------------------------------
    PRIMARY_COLOR = HexColor("#1E3A8A")   # Royal Slate Blue
    SECONDARY_COLOR = HexColor("#D97706")  # Warm Amber / Accent Gold
    TEXT_DARK = HexColor("#1F2937")        # Charcoal Body Text
    TEXT_MUTED = HexColor("#4B5563")       # Muted Contact Info
    
    styles = getSampleStyleSheet()
    
    # Main Name Header
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
    
    # BIGGER Category Headings (Increased from 16 to 18)
    heading_style = ParagraphStyle(
        name='SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=TA_LEFT,
        textColor=PRIMARY_COLOR,
        spaceBefore=6,                     # Padding adjusted since HRFlowable introduces its own space
        spaceAfter=10,
        keepWithNext=True                   # Holds heading together with content beneath it
    )
    
    # Job Title Style
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
    # 3. Parse & Build Document Flow
    # -------------------------------------------------------------------------
    story.append(Paragraph(derived_title.upper(), title_style))
    
    for line in lines:
        cleaned_line = line.strip()
        
        if not cleaned_line:
            continue
            
        if cleaned_line == derived_title:
            continue
            
        cleaned_line = (
            cleaned_line.replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')
        )
        
        # Convert Markdown Bold (**text**) to HTML inline bold tags
        cleaned_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_line)
        
        # A. Parse Major Categories with Thick Section Divider Lines
        if cleaned_line.startswith('###') or cleaned_line.startswith('##'):
            text = cleaned_line.lstrip('#').strip()
            
            # Draw strong structural rule lines between large categories
            if mode == "resume":
                story.append(HRFlowable(
                    width="100%", 
                    thickness=1.5,         # Bold architectural divider
                    color=PRIMARY_COLOR,   # Matches brand slate blue palette
                    spaceBefore=16,        # Generous breathing room above sections
                    spaceAfter=6
                ))
            story.append(Paragraph(text, heading_style))
            
        # B. Parse Bullet Points
        elif cleaned_line.startswith('- ') or cleaned_line.startswith('* ') or cleaned_line.startswith('• '):
            text = cleaned_line[2:].strip()
            bullet_text = f"<font color='{PRIMARY_COLOR.hexval()}'>&bull;</font> {text}"
            story.append(Paragraph(bullet_text, bullet_style))
            
        # C. Parse Standard Lines / Headers / Job Titles
        else:
            if '|' in cleaned_line:
                styled_meta = cleaned_line.replace('|', f" <font color='{SECONDARY_COLOR.hexval()}'>|</font> ")
                story.append(Paragraph(styled_meta, meta_style))
            
            elif mode == "resume" and (cleaned_line.startswith('<b>') or any(token in cleaned_line for token in ["Present", "202", "201"])):
                story.append(Paragraph(cleaned_line, job_title_style))
                
            else:
                story.append(Paragraph(cleaned_line, body_style))
                
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
