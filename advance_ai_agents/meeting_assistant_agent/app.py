import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

st.set_page_config(
    page_title="AI Meeting Assistant",
    page_icon="🎙️",
    layout="wide"
)

st.title("🎙️ AI Meeting Assistant")
st.caption("Powered by Google Gemini | Multimodal Audio, Transcripts & Action Matrix")

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

# Initialize Gemini Client
client = genai.Client(api_key=api_key) if api_key else None

with st.sidebar:
    st.header("⚙️ Configuration")
    if api_key:
        st.success("API Key detected from environment")
    else:
        user_key = st.text_input("Enter Google Gemini API Key", type="password")
        if user_key:
            client = genai.Client(api_key=user_key)
            st.success("Key applied!")

    st.markdown("---")
    st.markdown("### Input Source")
    input_mode = st.radio(
        "Choose Input Method:",
        [
            "Upload Audio / Voice Note (MP3, WAV, M4A)",
            "Record Voice Note (Microphone)",
            "Use Sample File (meeting_notes.txt)",
            "Upload Text File (.txt)",
            "Paste Text"
        ]
    )

    audio_bytes = None
    audio_mime = None
    text_content = ""

    if input_mode == "Upload Audio / Voice Note (MP3, WAV, M4A)":
        uploaded_audio = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a", "ogg"])
        if uploaded_audio:
            audio_bytes = uploaded_audio.read()
            audio_mime = uploaded_audio.type or "audio/mp3"
            st.audio(audio_bytes, format=audio_mime)
            st.success("Audio file loaded!")

    elif input_mode == "Record Voice Note (Microphone)":
        recorded_audio = st.audio_input("Record a meeting memo or note")
        if recorded_audio:
            audio_bytes = recorded_audio.read()
            audio_mime = recorded_audio.type or "audio/wav"
            st.audio(audio_bytes, format=audio_mime)
            st.success("Recording captured!")

    elif input_mode == "Use Sample File (meeting_notes.txt)":
        if os.path.exists("meeting_notes.txt"):
            with open("meeting_notes.txt", "r", encoding="utf-8") as f:
                text_content = f.read()
            st.info("Loaded default `meeting_notes.txt`")
        else:
            st.error("meeting_notes.txt not found in folder.")

    elif input_mode == "Upload Text File (.txt)":
        uploaded_file = st.file_uploader("Upload Notes", type=["txt"])
        if uploaded_file:
            text_content = uploaded_file.read().decode("utf-8")
            st.success("File uploaded successfully!")

    process_btn = st.button("🚀 Process Meeting", type="primary", use_container_width=True)

# Main screen paste box if selected
if input_mode == "Paste Text":
    text_content = st.text_area("Paste meeting transcript or notes here:", height=200)

PROMPT_INSTRUCTIONS = """
You are an executive scribe and meeting intelligence assistant.
Analyze the provided meeting input (which may be raw audio, voice notes, or text transcript).

Produce a clear, structured executive document containing:
1. Complete Transcript / Detailed Breakdown of all discussion points, technical scope, and budgets.
2. Executive Summary (High-level goals and context).
3. Decisions Matrix (Markdown table: Decision | Details).
4. Assigned Tasks Matrix (Markdown table: Task | Owner/Assignee | Deadline).
5. Immediate Next Steps.
"""

if process_btn:
    if not client:
        st.error("Please provide a valid Google Gemini API Key.")
    elif not audio_bytes and not text_content.strip():
        st.warning("Please provide an audio recording, uploaded file, or text input before processing.")
    else:
        with st.status("Gemini is listening and processing...", expanded=True) as status:
            try:
                contents = []
                
                # If audio input is supplied, attach it directly as inline binary parts
                if audio_bytes:
                    st.write("🎙️ Feeding raw audio directly into Gemini...")
                    contents.append(
                        types.Part.from_bytes(
                            data=audio_bytes,
                            mime_type=audio_mime
                        )
                    )
                
                # If text notes are supplied
                if text_content.strip():
                    st.write("📝 Ingesting text notes...")
                    contents.append(text_content)

                contents.append(PROMPT_INSTRUCTIONS)

                st.write("🧠 Generating transcript, decision matrix, and action plan...")
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=contents,
                )

                output_markdown = response.text

                # Save report locally
                with open("meeting_summary.md", "w", encoding="utf-8") as f:
                    f.write(output_markdown)

                status.update(label="Processing complete!", state="complete")

                # Display Results
                st.markdown("---")
                st.markdown(output_markdown)

                st.download_button(
                    label="📥 Download meeting_summary.md",
                    data=output_markdown,
                    file_name="meeting_summary.md",
                    mime="text/markdown"
                )

            except Exception as e:
                status.update(label="Execution encountered an error", state="error")
                st.error(f"Error processing input: {e}")

else:
    st.info("Choose your audio file, mic recording, or text in the sidebar, then click **Process Meeting**.")
    if text_content:
        with st.expander("Preview Selected Text"):
            st.text(text_content[:800] + ("..." if len(text_content) > 800 else ""))