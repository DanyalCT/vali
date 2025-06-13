# generate_report_llm.py
import os
from dotenv import load_dotenv
from google import genai


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_report(eval_text: str, pdf_text: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = (f"""
    Based on the following two pieces of information, generate a comprehensive report:

    1. Evaluation Summary (LLM generated):
    {eval_text}

    2. Extracted PDF Content:
    {pdf_text}

    The report should be structured, formal, and highlight key findings, strengths, weaknesses, and recommendations.
    """)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text