import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from io import BytesIO
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

# -----------------------------------------------------------------------------
# 1. Define the Expected Output Structure using Pydantic
# -----------------------------------------------------------------------------
class ApplicationMaterials(BaseModel):
    tailored_resume: str
    cover_letter: str
    interest_blurb: str

# -----------------------------------------------------------------------------
# 2. Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Application Material Tailorer",
    page_icon="💼",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. PDF Generation Helper Function (HTML to PDF via WeasyPrint)
# -----------------------------------------------------------------------------
def generate_pdf(content_text, document_title):
    """
    Advanced ReportLab PDF Generator.
    Parses Markdown syntax (headers, bold text, bullets) and converts them
    into perfectly styled, professional executive-level layouts.
    """
    buffer = BytesIO()
    
    # Page setup - 0.75-inch standard executive margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    story = []
    
    # -------------------------------------------------------------------------
    # Define Professional Typography & Styles (Times-Roman / Deep Corporate Palette)
    # -------------------------------------------------------------------------
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        name='DocTitle',
        fontName='Times-Bold',
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor='#111111',
        spaceAfter=4
    )
    
    # Subtitle for name/contact section
    meta_style = ParagraphStyle(
        name='DocMeta',
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor='#555555',
        spaceAfter=15
    )
    
    # Running Section Headings (e.g., Professional Experience, Education)
    heading_style = ParagraphStyle(
        name='SectionHeading',
        fontName='Times-Bold',
        fontSize=12,
        leading=16,
        alignment=TA_LEFT,
        textColor='#1A365D',  # Deep Slate Navy Accent
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True     # Prevents headings from getting orphaned at page bottoms
    )
    
    body_style = ParagraphStyle(
        name='DocBody',
        fontName='Times-Roman',
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )
    
    bullet_style = ParagraphStyle(
        name='DocBullet',
        fontName='Times-Roman',
        fontSize=10.5,
        leading=14,
        alignment=TA_LEFT,
        leftIndent=15,       # Indents bullet text cleanly
        firstLineIndent=-10, # Aligns the bullet symbol out to the left
        spaceAfter=4
    )

    # -------------------------------------------------------------------------
    # Process & Parse Text into Flowables
    # -------------------------------------------------------------------------
    lines = content_text.split('\n')
    
    # Document Header
    story.append(Paragraph(document_title.upper(), title_style))
    story.append(Spacer(1, 12))
    
    for line in lines:
        cleaned_line = line.strip()
        
        if not cleaned_line:
            continue
            
        # 1. Clean HTML characters so ReportLab doesn't crash on syntax symbols
        cleaned_line = (
            cleaned_line.replace('&', '&amp;')
                        .replace('<', '&lt;')
                        .replace('>', '&gt;')
        )
        
        # 2. Convert Markdown Bold (**text**) to HTML style tags (<b>text</b>)
        cleaned_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_line)
        
        # 3. Check for Headings (e.g., "### Experience" or "### Summary")
        if cleaned_line.startswith('###') or cleaned_line.startswith('##'):
            text = cleaned_line.lstrip('#').strip()
            story.append(Paragraph(text, heading_style))
            
        # 4. Check for Bullet Points (e.g., "- Built AI agents..." or "* Managed risk...")
        elif cleaned_line.startswith('- ') or cleaned_line.startswith('* ') or cleaned_line.startswith('• '):
            text = cleaned_line[2:].strip()
            # Insert a neat unicode bullet character
            bullet_text = f"&bull; {text}"
            story.append(Paragraph(bullet_text, bullet_style))
            
        # 5. Handle standard body text paragraphs
        else:
            # If it looks like a contact info string (contains | symbols), center align it
            if '|' in cleaned_line:
                story.append(Paragraph(cleaned_line, meta_style))
            else:
                story.append(Paragraph(cleaned_line, body_style))
                
    # Build the document template sequence
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
# -----------------------------------------------------------------------------
# 3. Password Protection Layer
# -----------------------------------------------------------------------------
def check_password():
    """Returns True if the user had the correct password."""
    # Ensure the password secret exists
    if "APP_PASSWORD" not in st.secrets:
        st.error("Security configuration error: 'APP_PASSWORD' is not set in secrets.")
        return False

    # Initialize password state if it doesn't exist
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    # If already authenticated, bypass login
    if st.session_state["password_correct"]:
        return True

    # Show login form
    st.title("🔒 Password Protected Application")
    password_input = st.text_input("Enter Password to access the tool:", type="password")
    
    if st.button("Log In"):
        if password_input == st.secrets["APP_PASSWORD"]:
            st.session_state["password_correct"] = True
            st.rerun()  # Refresh the page to show the full app immediately
        else:
            st.error("❌ Incorrect password. Please try again.")
            
    return False

# Stop execution here if the user hasn't authenticated
if not check_password():
    st.stop()

st.title("💼 AI Application Material Tailorer")
st.caption("Tailor your application materials instantly using OpenAI and your master resume.")

# -----------------------------------------------------------------------------
# 3. Retrieve Secrets & Initialize Client
# -----------------------------------------------------------------------------
# Fetch master resume and API key from Streamlit's secrets management
try:
    MASTER_RESUME = st.secrets["MASTER_RESUME"]
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except KeyError as e:
    st.error(f"Missing required secret: {e}. Please configure your `.streamlit/secrets.toml` file.")
    st.stop()

# Initialize the OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------------------------------------------------------
# 4. User Input UI
# -----------------------------------------------------------------------------
st.subheader("Target Job Description")
job_description = st.text_area(
    "Paste the job description or role requirements below:",
    height=300,
    placeholder="Looking for a Lead Data Scientist to use operations research skills, build AI agents..."
)

# -----------------------------------------------------------------------------
# 5. Generation Pipeline
# -----------------------------------------------------------------------------
if st.button("Generate Materials", type="primary"):
    if not job_description.strip():
        st.warning("Please paste a job description first!")
    else:
        with st.spinner("Analyzing job description and tailoring your profile..."):
            try:
                # Construct the system and user prompts
                system_prompt = (
                    "You are an expert executive career coach and technical writer. "
                    "Your task is to review a candidate's master resume and a target job description, "
                    "then generate optimized application materials."
                )
                
                user_prompt = f"""
                You are given a candidate's Master Resume and a Target Job Description. 
                
                Please generate three distinct items:
                1. **Resume**: Optimize the bullet points, summaries, and skills from the Master Resume to highlight the most relevant technical and strategic alignment with the Target Job Description. Do not invent false experience.
                2. **Cover Letter**: Write a compelling, highly professional cover letter matching the candidate's exact background to the key themes of the job description. Keep it to 3 paragraphs. Use Master Resume.
                3. **Interest Blurb**: Write a concise, one paragraph response to the standard prompt: "Why are you interested in this position/company?". Make it punchy, authentic, and metric-focused where possible.

                ---
                ### MASTER RESUME
                {MASTER_RESUME}

                ---
                ### TARGET JOB DESCRIPTION
                {job_description}
                """

                # Call OpenAI with Structured Outputs
                response = client.beta.chat.completions.parse(
                    model="gpt-5.4-mini",  # or gpt-4o-mini for speed/cost efficiency
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format=ApplicationMaterials,
                    temperature=0.7
                )
                
                # Extract the structured response object
                materials = response.choices[0].message.parsed
                
                # Store results in session state so they persist across tab switches
                st.session_state["results"] = materials
                st.success("Materials successfully generated!")

            except Exception as e:
                st.error(f"An error occurred during generation: {e}")

# -----------------------------------------------------------------------------
# 6. Display the Outputs via Tabs
# -----------------------------------------------------------------------------
if "results" in st.session_state:
    materials = st.session_state["results"]
    
    st.markdown("---")
    st.subheader("Your Generated Materials")
    
    # Create clean layout tabs
    tab1, tab2, tab3 = st.tabs(["📄 Cover Letter", "🎯 Why This Role?", "📝 Tailored Resume"])
    
    with tab1:
        st.markdown("### Cover Letter")

        cl_pdf_bytes = generate_pdf(materials.cover_letter, "Cover Letter")
        
        st.download_button(
            label="⬇️ Download Cover Letter PDF",
            data=cl_pdf_bytes,
            file_name="Cover_Letter.pdf",
            mime="application/pdf"
        )
        st.text_area("Copy Cover Letter", value=materials.cover_letter, height=500)
        
    with tab2:
        st.markdown("### Why are you interested?")
        st.text_area("Copy Blurb", value=materials.interest_blurb, height=250)
        
    with tab3:
        st.markdown("### Tailored Resume Suggestion")

        resume_pdf_bytes = generate_pdf(materials.tailored_resume, "Tailored Resume")
        
        st.download_button(
            label="⬇️ Download Resume PDF",
            data=resume_pdf_bytes,
            file_name="Tailored_Resume.pdf",
            mime="application/pdf"
        )
        st.text_area("Copy Tailored Resume", value=materials.tailored_resume, height=600)
