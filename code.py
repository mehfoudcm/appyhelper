import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from io import BytesIO
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor

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
def generate_pdf(content_text, mode="resume"):
    """
    Polished & Colorful ReportLab PDF Generator.
    
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
    # 2. Define Palette & Typography (Configured by Document Type Mode)
    # -------------------------------------------------------------------------
    PRIMARY_COLOR = HexColor("#1E3A8A")   # Royal Slate Blue
    SECONDARY_COLOR = HexColor("#D97706")  # Warm Amber / Accent Gold
    TEXT_DARK = HexColor("#1F2937")        # Charcoal Body Text
    TEXT_MUTED = HexColor("#4B5563")       # Muted Contact Info
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        textColor=PRIMARY_COLOR,
        spaceAfter=4
    )
    
    meta_style = ParagraphStyle(
        name='DocMeta',
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        alignment=TA_CENTER,
        textColor=TEXT_MUTED,
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        name='SectionHeading',
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=18,
        alignment=TA_LEFT,
        textColor=PRIMARY_COLOR,
        spaceBefore=16,
        spaceAfter=6,
        keepWithNext=True
    )
    
    # MODE SWITCH: Cover letters look cleaner left-aligned; Resumes look great justified
    body_style = ParagraphStyle(
        name='DocBody',
        fontName='Helvetica',
        fontSize=10.5 if mode == "cover_letter" else 10,
        leading=15 if mode == "cover_letter" else 14.5,
        alignment=TA_LEFT if mode == "cover_letter" else TA_JUSTIFY,
        textColor=TEXT_DARK,
        spaceAfter=10 if mode == "cover_letter" else 5  # More breathing room between letter paragraphs
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
        
        cleaned_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cleaned_line)
        
        # Parse Headings
        if cleaned_line.startswith('###') or cleaned_line.startswith('##'):
            text = cleaned_line.lstrip('#').strip()
            
            # MODE SWITCH: Only include colored line rules for highly categorized resumes
            if mode == "resume":
                story.append(HRFlowable(
                    width="100%", 
                    thickness=1, 
                    color=HexColor("#E5E7EB"), 
                    spaceBefore=10, 
                    spaceAfter=6
                ))
            story.append(Paragraph(text, heading_style))
            
        # Parse Bullet Points
        elif cleaned_line.startswith('- ') or cleaned_line.startswith('* ') or cleaned_line.startswith('• '):
            text = cleaned_line[2:].strip()
            bullet_text = f"<font color='{PRIMARY_COLOR.hexval()}'>&bull;</font> {text}"
            story.append(Paragraph(bullet_text, bullet_style))
            
        # Parse Standard Lines / Headers
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
                1. **Resume**: Create several (2 to 4) bullet points, summaries, and skills to highlight the most relevant technical and strategic alignment with the Target Job Description to pass ATS (applicant tracking system).
                               Pick appropriate title names based on information provided. Use the Master Resume to align specific experience.
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
                    model="gpt-5.4",  # or gpt-4o-mini for speed/cost efficiency
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
    tab1, tab2, tab3 = st.tabs(["📄 Cover Letter", "🎯 Why This Role?", "📝 Resume"])
    
    with tab1:
        st.markdown("### Cover Letter")

        cl_pdf_bytes = generate_pdf(materials.cover_letter, mode = "cover_letter")
        
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
        st.markdown("### Resume Suggestion")

        resume_pdf_bytes = generate_pdf(materials.tailored_resume, mode="resume")
        
        st.download_button(
            label="⬇️ Download Resume PDF",
            data=resume_pdf_bytes,
            file_name="Tailored_Resume.pdf",
            mime="application/pdf"
        )
        st.text_area("Copy Tailored Resume", value=materials.tailored_resume, height=600)
