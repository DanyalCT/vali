# Placeholder for Gemini LLM integration
import os
from dotenv import load_dotenv
load_dotenv()
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key")

def generate_questions_from_text(text: str, num_questions: int = 47) -> list:
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
    questions = [
        "What is the total number of founders?",
    "How many founders work full-time on the project?",
    "Do the founders have previous startup or entrepreneurial experience?",
    "Is there a technical founder on the team?",
    "How long has the founding team been working together?",
    "Do the founders have relevant industry experience?",
    "Are there any advisors or mentors actively involved?",
    "How many full-time employees are currently working for the company?",
    "What is your main source of revenue?",
    "How do you acquire customers?",
    "What is your average customer acquisition cost (CAC)?",
    "What is your customer lifetime value (LTV)?",
    "Do you operate in a B2B, B2C, or B2B2C model?",
    "Is your product or service scalable across markets?",
    "What are your gross margins?",
    "How do you plan to grow revenue over the next 3 years?",
    "What is your current monthly recurring revenue (MRR), if any?",
    "What is the current stage of your product? (idea, MVP, launched, generating revenue)",
    "Do you have users or customers? If yes, how many?",
    "What problem does your product solve?",
    "How is your product or service different from competitors?",
    "What feedback have you received from users?",
    "Do you have a clear product development roadmap?",
    "What are the biggest risks to your product development?",
    "What is the estimated size of your target market?",
    "What is your estimated market share in 3 years?",
    "Who are your main competitors?",
    "What differentiates you from existing competitors?",
    "What barriers to entry exist in your industry?",
    "Are there any current trends that support your growth?",
    "Have you registered any intellectual property (IP), trademarks, or patents?",
    "Do you own the rights to all of your code and content?",
    "Are there any ongoing legal issues or disputes?",
    "Is your startup properly incorporated?",
    "Do you have signed contracts with customers or partners?",
    "Are you compliant with data protection and other applicable regulations (e.g., GDPR)?",
    "What are the top 3 risks facing your business today?",
    ]
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
    print(questions)
    return questions[:num_questions] 