import os
import time
from agno.agent import Agent
from agno.models.google import Gemini
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please set GOOGLE_API_KEY in your .env file.")

# Read meeting notes directly
notes_file = "meeting_notes.txt"
if os.path.exists(notes_file):
    with open(notes_file, "r", encoding="utf-8") as f:
        notes_content = f.read()
else:
    notes_content = "No meeting notes found."

# Initialize Gemini
model = Gemini(id="gemini-3.6-flash", api_key=api_key)

def run_agent_with_retry(agent, prompt, max_retries=3, delay=3):
    """Executes an agent run with backoff on transient errors."""
    for attempt in range(max_retries):
        try:
            response = agent.run(prompt)
            # Agno returns an object; check if error text slipped through
            resp_text = str(response.content if hasattr(response, "content") else response)
            if "503" in resp_text or "UNAVAILABLE" in resp_text:
                raise RuntimeError(f"Transient 503 detected: {resp_text}")
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            print(f"Warning: Attempt {attempt + 1} encountered an issue ({e}). Retrying in {delay * (2 ** attempt)}s...")
            time.sleep(delay * (2 ** attempt))

# Agent 1: Analyzes and creates detailed summary
transcription_agent = Agent(
    name="Meeting Analysis Agent",
    model=model,
    instructions=(
        "You are an expert executive scribe. Analyze the provided meeting notes. "
        "Extract key discussion points, technical decisions, cost structures, and deadlines, "
        "and produce a comprehensive, structured markdown summary."
    ),
    markdown=True,
)

# Agent 2: Synthesizes Action Items & Decisions Table
summary_agent = Agent(
    name="Meeting Summary Agent",
    model=model,
    instructions=(
        "You are an executive summarization assistant. "
        "Review the meeting details and produce a crisp executive report containing:\n"
        "1. Executive Summary of key topics\n"
        "2. Decisions Matrix (Decision vs Details table)\n"
        "3. Assigned Tasks Matrix (Task, Owner/Assignee, Deadline table)\n"
        "4. Next immediate steps."
    ),
    markdown=True,
)

if __name__ == "__main__":
    print("Starting Meeting Intelligence Agent...")
    try:
        print("\n--- Step 1: Processing Notes & Generating Summary ---")
        step1_prompt = f"Analyze these notes and provide a structured summary:\n\n{notes_content}"
        res1 = run_agent_with_retry(transcription_agent, step1_prompt)
        
        # Save summary to file
        with open("meeting_summary.md", "w", encoding="utf-8") as f:
            f.write(str(res1.content if hasattr(res1, "content") else res1))
        print("Summary written to meeting_summary.md")
        
        print("\n--- Step 2: Executive Action Plan & Task Matrix ---")
        step2_prompt = f"Review these notes and generate the decision/task matrices:\n\n{notes_content}"
        res2 = run_agent_with_retry(summary_agent, step2_prompt)
        
        if hasattr(res2, "content"):
            print(res2.content)
        else:
            print(res2)
            
    except Exception as e:
        print(f"Execution stopped: {e}")