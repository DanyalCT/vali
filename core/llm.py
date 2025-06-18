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
    # 1. Team & Founders
    "What is the total number of founders?",
    "How many founders work full-time on the project?",
    "Do the founders have previous startup or entrepreneurial experience?",
    "Is there a technical founder on the team?",
    "How long has the founding team been working together?",
    "Do the founders have relevant industry experience?",
    "Are there any advisors or mentors actively involved?",
    "How many full-time employees are currently working for the company?",
    "What is the average age of your founders?", # NEW
    "Could you describe your current shareholders? For example, are they primarily founders, angel investors, venture capitalists, or employees?", # NEW

    # 2. Business Model & Strategy
    "What is your main source of revenue?",
    "How do you acquire customers?",
    "What is your average customer acquisition cost (CAC)?",
    "What is your customer lifetime value (LTV)?",
    "Do you operate in a B2B, B2C, or B2B2C model?",
    "Is your product or service scalable across markets?",
    "What are your gross margins?",
    "How do you plan to grow revenue over the next 3 years?",
    "What is your projected annual revenue growth rate for the next three years? (e.g., 50%, 75%, 100%)", # NEW
    "What is your current monthly recurring revenue (MRR), if applicable?", # NEW (re-emphasized for clarity)

    # 3. Product or Service
    "What is the current stage of your product? (idea, MVP, launched, generating revenue)",
    "Do you have users or customers? If yes, how many?",
    "What problem does your product solve?",
    "How is your product or service different from competitors?",
    "What feedback have you received from users?",
    "Do you have a clear product development roadmap?",
    "What are the biggest risks to your product development?",

    # 4. Market & Industry
    "What is the estimated size of your target market?",
    "What is your estimated market share in 3 years?",
    "Who are your main competitors?",
    "What differentiates you from existing competitors?",
    "What barriers to entry exist in your industry?",
    "Are there any current trends that support your growth?",
    "What is the estimated annual growth rate of your target market? (e.g., 15% per year)", # NEW

    # 5. Legal, IP & Risk
    "Have you registered any intellectual property (IP), trademarks, or patents?",
    "Do you own the rights to all of your code and content?",
    "Are there any ongoing legal issues or disputes?",
    "Is your startup properly incorporated?",
    "Do you have signed contracts with customers or partners?",
    "Are you compliant with data protection and other applicable regulations (e.g., GDPR)?",
    "Are you compliant with all relevant data protection (e.g., GDPR, CCPA) and any other industry-specific regulations applicable to your business? (e.g., HIPAA for healthcare, PCI DSS for payments)", # NEW (re-emphasized for clarity)
    "What are the top 3 most significant risks currently facing your business?", # NEW (re-emphasized for clarity)

    # 6. Financial Inputs for Valuation Methods (New Category)
    "What is the average EBITDA multiple for companies in your industry? (e.g., 10x, 12x)", # NEW
    "What is the Beta specific to your industry or for a publicly traded company comparable to yours?", # NEW
    "What is the current risk-free rate you are using for valuation purposes? (e.g., the yield on a 10-year U.S. Treasury bond, like 4.5%)", # NEW
    "What market risk premium are you using for your valuation? (e.g., 5% - this is the expected return of the market minus the risk-free rate)", # NEW
    "What is the annual required Return on Investment (ROI) expected by potential investors in your company? (e.g., 25%, 30%)", # NEW
    "Do you have any historical non-operating cash? If so, what was its value? (This refers to cash not directly used for core business operations).", # NEW
    "Do you have any financial assets other than cash and cash equivalents? If so, what is their value?", # NEW
    "Do you have any deferred tax assets? If so, what is their value?", # NEW
    "What illiquidity discount rate are you applying to your valuation? (This accounts for the difficulty of quickly converting private equity to cash, e.g., 15%, 20%)", # NEW
    "Please provide your estimated survival rates for each of the following years. This helps us account for the risk of early-stage startups not surviving. Year 1: ____% Year 2: ____% Year 3: ____% Year 4: ____% Year 5: ____% Year 6: ____% Year 7: ____% Year 8: ____% Year 9: ____% Year 10: ____%", # NEW (combined into one string for list item)
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