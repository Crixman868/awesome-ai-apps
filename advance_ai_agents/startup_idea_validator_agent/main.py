import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Google API Key not found. Please set GOOGLE_API_KEY in your .env file.")

client = genai.Client(api_key=api_key)

# Primary model and resilient fallback models
CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
]


def run_validation(idea: str) -> str:
    """
    Validates a startup concept across market sizing, competitive moats,
    revenue models, risks, and next steps with multi-model fallback.
    """
    prompt = f"""
    You are a venture capitalist and startup strategist conducting a rigorous due-diligence assessment.
    
    Startup Idea:
    "{idea}"

    Provide a complete, deeply detailed Startup Validation Report formatted in Markdown.
    
    Structure your report with the following sections:

    # 🚀 Startup Idea Validation: {idea}

    ## 1. 💡 Concept Refinement & Value Proposition
    - **Core Problem Statement**: Specific pain points being addressed.
    - **Target Customer Archetype**: Who feels this pain most acutely?
    - **Unique Value Proposition (UVP)**: Why this solution is 10x better than existing workflows.

    ## 2. 📊 Market Opportunity & Sizing
    - **Total Addressable Market (TAM)**: Industry scale and trajectory.
    - **Serviceable Addressable Market (SAM)**: Reachable initial market.
    - **Target Customer Segments**: Primary, secondary, and niche early adopters.
    - **Current Market Drivers & Headwinds**: Tailwinds accelerating adoption and risks slowing it down.

    ## 3. 🛡️ Competitive Landscape & Defensibility
    - **Direct Competitors**: Incumbents and emerging startups in this space.
    - **Indirect / Substitute Competitors**: Existing manual workflows or spreadsheet hacks.
    - **Competitive Moat**: Data flywheels, network effects, proprietary tech, or high switching costs.

    ## 4. 💰 Revenue Model & Unit Economics
    - **Monetization Mechanics**: Pricing models (SaaS tiers, usage-based, transaction fee, enterprise licensing).
    - **Estimated CAC vs. LTV Dynamics**: Expected customer acquisition dynamics.

    ## 5. ⚠️ Critical Risks & Pre-Mortem Analysis
    - **Adoption / Distribution Risk**: Why customers might hesitate to onboard.
    - **Technical / Operational Risk**: Feasibility and execution bottlenecks.
    - **Mitigation Strategies**: Actionable tactics to de-risk each factor.

    ## 6. 🏁 Strategic Verdict & Next Steps
    - **Validation Verdict**: (Proceed, Pivot, or Abandon) with reasoning.
    - **Week 1-4 Action Checklist**: Low-cost MVP and customer discovery tests to execute immediately.

    ---
    *Disclaimer: This assessment is generated for strategic planning and validation purposes.*
    """

    last_error = ""

    for model_name in CANDIDATE_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response.text:
                    return f"> *Model used: `{model_name}`*\n\n" + response.text

            except Exception as e:
                err_str = str(e)
                last_error = err_str

                # If it's a 503 high-demand spike, sleep 3s then try fallback model
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    time.sleep(3)
                    continue

                # If quota limit hit, pass to next attempt
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    time.sleep(5)
                    continue

    return f"### Error running validation\n\n`{last_error}`"


if __name__ == "__main__":
    test_idea = "A local micro-warehouse tracking app for container freight clearance and pallet management"
    print(run_validation(test_idea))