from report_agent.personas import personas
import os
from pymongo import MongoClient
import json
import re

def get_user_context(user_id):
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["valoov_ai_db"]
    pdf_texts = list(db["pdf_texts"].find({"user_id": user_id}))
    user_qas = list(db["user_qas"].find({"user_id": user_id}))
    return pdf_texts, user_qas

def save_report_data(user_id, result):
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client["valoov_ai_db"]
    # If result is a string, clean and parse it to dict
    if isinstance(result, str):
        # Remove markdown code block if present
        cleaned = re.sub(r"^```json|```$", "", result, flags=re.MULTILINE).strip()
        try:
            result = json.loads(cleaned)
        except Exception:
            result = {"raw": cleaned}
    db["report_data"].update_one(
        {"user_id": user_id},
        {"$push": {"results": result}},
        upsert=True
    )

def agent(prompt: str, api_key: str):
    try:
        from google import genai
    except ImportError:
        return {"error": "google-genai library not installed."}
    if not api_key:
        return {"error": "API key not provided."}
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=prompt
    )
    return getattr(response, 'text', str(response))

def process_personas(user_id, api_key):
    pdf_texts, user_qas = get_user_context(user_id)
    context = f"PDF Texts: {pdf_texts}\nUser QAs: {user_qas}"
    results = []
    for idx, persona in enumerate(personas):
        prompt = f"{persona['description']}\n\nContext:\n{context}"
        result = agent(prompt, api_key)
        print(f"Persona: {persona['name']} | Role: {persona['role']}\nPrompt: {prompt}\nResponse: {result}\n{'-'*40}")
        # Save only the response for each agent
        save_report_data(user_id, result)
        results.append({
            "persona": persona["name"],
            "role": persona["role"],
            "response": result
        })
    return {"results": results} 