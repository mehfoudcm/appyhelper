import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from weasyprint import HTML

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
    Converts plain text content into a beautifully formatted PDF using WeasyPrint.
    Uses standard print-safe typography and explicit A4 paged media styling.
    """
    # Replace newlines with HTML line breaks or paragraphs safely
    formatted_content = "".join(
        f"<p>{line.strip()}</p>" if line.strip() else "<br/>"
        for line in content_text.split("\n")
    )

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{document_title}</title>
        <style>
            @page {{
                size: A4;
                margin: 20mm 15mm;
                background-color: #ffffff;
            }}
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                padding: 0;
                font-family: 'Times New Roman', Times, serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #222222;
            }}
            p {{
                margin: 0 0 12pt 0;
                text-align: justify;
            }}
            br {{
                content: "";
                display: block;
                margin-bottom: 12pt;
            }}
            h1, h2, h3 {{
                color: #111111;
                margin-top: 0;
            }}
        </style>
    </head>
    <body>
        {formatted_content}
    </body>
    </html>
    """
    # Compile the HTML template directly to bytes in memory
    return HTML(string=html_template).write_pdf()

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
                1. **Tailored Resume**: Optimize the bullet points, summaries, and skills from the Master Resume to highlight the most relevant technical and strategic alignment with the Job Description. Do not invent false experience.
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
                    model="gpt-4o",  # or gpt-4o-mini for speed/cost efficiency
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
        st.download_button(
            label="⬇️ Download Resume PDF",
            data=resume_pdf_bytes,
            file_name="Tailored_Resume.pdf",
            mime="application/pdf"
        )
        st.text_area("Copy Tailored Resume", value=materials.tailored_resume, height=600)
