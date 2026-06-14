import streamlit as st
from openai import OpenAI
from pydantic import BaseModel

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
    placeholder="Looking for a Lead Data Scientist to optimize credit risk, build AI agents..."
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
                2. **Cover Letter**: Write a compelling, highly professional cover letter matching the candidate's exact background to the key themes of the job description.
                3. **Interest Blurb**: Write a concise, 1-2 paragraph response to the standard prompt: "Why are you interested in this position/company?". Make it punchy, authentic, and metric-focused where possible.

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
        st.text_area("Copy Cover Letter", value=materials.cover_letter, height=500)
        
    with tab2:
        st.markdown("### Why are you interested?")
        st.text_area("Copy Blurb", value=materials.interest_blurb, height=250)
        
    with tab3:
        st.markdown("### Tailored Resume Suggestion")
        st.text_area("Copy Tailored Resume", value=materials.tailored_resume, height=600)
