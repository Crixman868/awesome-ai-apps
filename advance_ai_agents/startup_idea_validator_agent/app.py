import os
import streamlit as st
from dotenv import load_dotenv
import main as validator_main

load_dotenv()

st.set_page_config(
    page_title="AI Startup Idea Validator",
    page_icon="🚀",
    layout="wide"
)

# Custom Styling
st.markdown(
    """
    <style>
    .report-card {
        padding: 1.2rem;
        background-color: #f8f9fa;
        border-radius: 8px;
        border-left: 5px solid #2b70e4;
        margin-bottom: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style="padding: 0.5rem 0 1.2rem 0; border-bottom: 2px solid #f0f2f6; margin-bottom: 1.5rem;">
        <h1 style="margin: 0; font-size: 2.2rem;">🚀 AI Startup Idea Validator</h1>
        <p style="margin: 0.3rem 0 0 0; color: #555; font-size: 1.05rem;">
            Venture-grade feasibility analysis, market sizing (TAM/SAM), competitive defensibility, and MVP execution roadmaps.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize Session State
if "report" not in st.session_state:
    st.session_state.report = None
if "current_idea" not in st.session_state:
    st.session_state.current_idea = ""

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Settings")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=os.getenv("GOOGLE_API_KEY", ""),
        type="password",
        help="Reads from your .env file or input here."
    )
    if api_key_input:
        os.environ["GOOGLE_API_KEY"] = api_key_input
        validator_main.api_key = api_key_input

    st.markdown("---")
    st.subheader("📋 Evaluation Methodology")
    st.markdown(
        """
        - **Value Prop & UVP**: Problem severity & differentiation
        - **Market Sizing**: TAM, SAM, and niche beachheads
        - **Moats & Defensibility**: Switching costs & network effects
        - **Unit Economics**: Pricing models, CAC/LTV dynamics
        - **Pre-Mortem**: Core execution and adoption risks
        - **Action Roadmap**: Week 1–4 customer discovery tests
        """
    )
    st.markdown("---")
    if st.button("Clear Report / Reset", use_container_width=True):
        st.session_state.report = None
        st.session_state.current_idea = ""
        st.rerun()

# User Input Container
st.subheader("💡 Startup or Product Concept")

sample_ideas = [
    "Custom idea...",
    "A local micro-warehouse tracking app for container freight clearance and pallet management",
    "An automated customs tariff classification and CARICOM compliance platform for logistics brokers",
    "An AI-assisted code review and linting agent tailored for small engineering teams",
    "An on-demand mobile automotive brake caliper and rotor mobile servicing service"
]

selected_template = st.selectbox("Select an industry template or choose 'Custom idea...':", sample_ideas)
default_text = "" if selected_template == "Custom idea..." else selected_template

idea_input = st.text_area(
    "Describe the problem, target audience, and proposed product workflow:",
    value=default_text,
    height=120,
    placeholder="E.g., A mobile logistics platform that allows container dispatchers to track customs clearance milestones, verify bill of lading documents, and invoice brokers instantly..."
)

col_run, col_status = st.columns([1, 4])
with col_run:
    submit_btn = st.button("🚀 Validate Concept", type="primary", use_container_width=True)

if submit_btn:
    if not idea_input.strip():
        st.warning("Please enter a concept description first.")
    else:
        with st.spinner("Running due-diligence models across market sizing, defensibility, and unit economics..."):
            result = validator_main.run_validation(idea_input.strip())
            st.session_state.report = result
            st.session_state.current_idea = idea_input.strip()

# Render Generated Report
if st.session_state.report:
    report_text = st.session_state.report

    st.markdown("---")
    header_col, dl_col1, dl_col2 = st.columns([4, 1.2, 1.2])
    with header_col:
        st.subheader("📊 Validation Dossier")
    with dl_col1:
        st.download_button(
            label="📥 Download .MD",
            data=report_text,
            file_name="startup_validation_report.md",
            mime="text/markdown",
            use_container_width=True
        )
    with dl_col2:
        st.download_button(
            label="📄 Download .TXT",
            data=report_text,
            file_name="startup_validation_report.txt",
            mime="text/plain",
            use_container_width=True
        )

    # Multi-tab layout for easy navigation
    tab_full, tab_raw = st.tabs(["📑 Structured Report", "💻 Raw Markdown"])

    with tab_full:
        st.markdown(report_text)

    with tab_raw:
        st.code(report_text, language="markdown")