import os
import io
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from google import genai

load_dotenv()

st.set_page_config(
    page_title="Candilyzer - CV & Applicant Screening Engine",
    page_icon="📄",
    layout="wide"
)

# API Setup
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
]


def extract_text_from_pdf(pdf_file) -> str:
    """Extracts plain text from an uploaded PDF file handle."""
    try:
        reader = PdfReader(pdf_file)
        full_text = []
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                full_text.append(page_text)
        return "\n".join(full_text).strip()
    except Exception as e:
        return f"Error reading PDF file: {str(e)}"


def evaluate_applicant(client: genai.Client, job_title: str, jd_text: str, candidate_name: str, cv_text: str) -> str:
    """Evaluates candidate CV against role requirements using structured dimensions."""
    prompt = f"""
    You are an executive talent screener and hiring manager evaluating an applicant.
    
    Target Role: {job_title}

    Job Description & Requirements:
    \"\"\"{jd_text.strip() if jd_text.strip() else "Standard industry qualifications and operational competency for this title."}\"\"\"

    Candidate Identifier: {candidate_name}

    Applicant CV Content:
    \"\"\"{cv_text}\"\"\"

    Conduct an objective, thorough evaluation across technical, operational, and practical qualifications.
    Output a structured Markdown screening report formatted exactly as follows:

    # 📄 Applicant Evaluation: {candidate_name}
    **Target Role:** {job_title}  
    **Match Alignment Score:** [Provide a bold score e.g. **84/100**]  
    **Recruiter Verdict:** [SHORTLIST FOR INTERVIEW / HOLD AS BACKUP / REGRET]

    ---

    ## 1. 🎯 Executive Screening Summary
    - Concise 2-3 sentence assessment of candidate fit, professional maturity, and core background relevance.

    ## 2. 📋 Core Criteria & Qualifications Matrix
    | Job Requirement / Competency | Candidate Demonstrated Experience | Match Status | Notes |
    | :--- | :--- | :--- | :--- |
    [List 5 to 7 key criteria extracted from the Job Description and assess whether the CV demonstrates direct, partial, or no evidence]

    ## 3. 🌟 Standout Strengths & Direct Value-Add
    - **Demonstrated Competency 1**: Concrete evidence and achievements from past roles.
    - **Demonstrated Competency 2**: Transferable skills or tools relevant to this position.
    - **Demonstrated Competency 3**: Operational or organizational execution depth.

    ## 4. ⚠️ Gaps, Missing Prerequisites & Verification Flags
    - Highlight missing certifications, unaddressed technical proficiencies, employment gaps, or vague responsibility claims.

    ## 5. 🎙️ Tailored Interview Validation Questions
    Provide 4 sharp, contextual interview questions designed to test claims made on the CV:
    1. **[Core Execution Probe]**: Verify hands-on depth in a primary skill claimed.
    2. **[Problem Solving / Crisis Probe]**: Situational question based on their past work environment.
    3. **[Requirement Gap Probe]**: Directly target an area where the CV was weak or ambiguous.
    4. **[Operational / Workflow Verification]**: Ask for specific metrics, tools, or procedures used in a prior role.

    ## 6. 🏁 Hiring Recommendation & Next Action
    - **Immediate Action**: Specific recommendation for HR / Hiring Committee (e.g. Schedule phone screen, request portfolio/references, or decline).
    """

    for model_name in CANDIDATE_MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response.text:
                return f"> *Analysis Engine: `{model_name}`*\n\n" + response.text
        except Exception:
            continue

    return "### Error running applicant evaluation\nCould not connect to Gemini models. Check your API key and connection."


# --- Streamlit UI Layout ---

st.markdown(
    """
    <div style="padding: 0.5rem 0 1.2rem 0; border-bottom: 2px solid #f0f2f6; margin-bottom: 1.5rem;">
        <h1 style="margin: 0; font-size: 2.2rem;">📄 Candilyzer: CV & Applicant Screening Engine</h1>
        <p style="margin: 0.3rem 0 0 0; color: #555; font-size: 1.05rem;">
            Automated PDF resume parser and candidate-to-job calibration engine for rapid recruitment shortlisting.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.header("⚙️ Configuration")
    user_key = st.text_input(
        "Google Gemini API Key",
        value=api_key or "",
        type="password",
        help="Reads from your .env file or enter one here."
    )
    if user_key:
        api_key = user_key

    st.markdown("---")
    st.subheader("📋 Evaluation Dimensions")
    st.markdown(
        """
        - **Alignment Score**: Objective match against the specific JD
        - **Criteria Matrix**: Requirement-by-requirement verification
        - **Value-Add Strengths**: Documented achievements & direct impact
        - **Flagged Gaps**: Missing qualifications, ambiguities, or risks
        - **Interview Probes**: Targeted questions to verify CV claims
        - **Hiring Verdict**: Shortlist, Hold, or Regret
        """
    )
    st.markdown("---")
    st.caption("Supports multi-page PDF CVs across operations, logistics, administration, IT, finance, and engineering.")

if not api_key:
    st.error("⚠️ Please provide a Google Gemini API Key in the sidebar or via your .env file.")
    st.stop()

gemini_client = genai.Client(api_key=api_key)

col_role, col_cv = st.columns([1, 1], gap="large")

with col_role:
    st.subheader("📌 1. Target Role & Requirements")
    job_title = st.text_input(
        "Job Title / Position",
        value="Customs Logistics & Freight Operations Coordinator",
        placeholder="e.g. Warehouse Supervisor, Accounts Officer, Python Developer"
    )
    
    jd_input = st.text_area(
        "Paste Job Description & Key Criteria (Must-haves & Nice-to-haves):",
        value="""Key Responsibilities:
- Manage customs clearance documentation, CARICOM invoices, and bills of lading.
- Coordinate container transport logistics, warehouse receipting, and freight inspection schedules.
- Liaison with customs brokerage agents, port authorities, and shipping lines.

Must-Have Requirements:
- Minimum 3-5 years hands-on experience in freight forwarding or import/export logistics.
- Working knowledge of ASYCUDA World or regional customs clearance portals.
- Strong organizational skills, spreadsheet proficiency, and document accuracy.""",
        height=260,
        placeholder="Paste requirements, certifications, required years of experience, and responsibilities..."
    )

with col_cv:
    st.subheader("👤 2. Candidate Dossier")
    candidate_name = st.text_input("Applicant Name / Tracking ID", value="Applicant 1")
    
    uploaded_pdf = st.file_uploader("Upload Candidate CV (PDF format)", type=["pdf"])
    
    pasted_cv = st.text_area(
        "Or Paste CV / Resume Text Directly (Optional if PDF uploaded):",
        height=180,
        placeholder="If you don't have a PDF, paste resume text here..."
    )

st.markdown("---")
if st.button("🚀 Analyze Applicant Fit", type="primary", use_container_width=True):
    extracted_text = ""

    if uploaded_pdf is not None:
        with st.spinner("Extracting text from uploaded PDF..."):
            extracted_text = extract_text_from_pdf(uploaded_pdf)
    elif pasted_cv.strip():
        extracted_text = pasted_cv.strip()

    if not extracted_text:
        st.warning("⚠️ Please upload a PDF CV or paste resume text to begin evaluation.")
    elif not job_title.strip():
        st.warning("⚠️ Please provide a target job title.")
    else:
        with st.spinner("Running deep candidate-to-role calibration..."):
            report = evaluate_applicant(
                client=gemini_client,
                job_title=job_title,
                jd_text=jd_input,
                candidate_name=candidate_name,
                cv_text=extracted_text
            )

            col_res_header, col_dl = st.columns([4, 1.2])
            with col_res_header:
                st.subheader("📊 Screening Dossier & Hiring Recommendation")
            with col_dl:
                st.download_button(
                    label="📥 Download Report (.md)",
                    data=report,
                    file_name=f"{candidate_name.replace(' ', '_')}_screening_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )

            st.markdown(report)