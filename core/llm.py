# Placeholder for Gemini LLM integration
import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key")

def generate_questions_from_text(text: str, num_questions: int = 10) -> list:
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = (
        f"Read the following document and generate {num_questions} important questions that a human should be able to answer after reading it. "
        f"Return only the questions as a numbered list.\n\nDocument:\n{text}"
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    # Extract questions from response.text (assuming numbered list)
    questions = []
    if hasattr(response, "text"):
        for line in response.text.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                # Remove number/bullet
                q = line.lstrip("0123456789.-• ")
                if q:
                    questions.append(q)
    # Fallback: if nothing parsed, return the whole response as one question
    if not questions and hasattr(response, "text"):
        questions = [response.text.strip()]
    return questions[:num_questions] 