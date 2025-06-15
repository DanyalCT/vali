# crud.py
from db.mongodb import db
from models.question import UserQA
from models.PDFMODEL import PDFFORMAT
import json

def save_user_qa(user_qa: UserQA, pdf_id: str):
    db.user_qas.update_one(
        {"user_id": user_qa.user_id},
        {"$set": {
            "user_qa":user_qa.model_dump(),
            "pdf_id": pdf_id
        }},
        upsert=True
    )
    
def save_pdf_text(user_id: str, pdf_text: str):
    result = db.pdf_texts.update_one(
        {"user_id": user_id},
        {"$set": {"pdf_text": pdf_text}},
        upsert=True
    )
    if result.upserted_id:
        return str(result.upserted_id)
    else:
        # If document was updatPDF(not inserted), find and retur.pdf_texts
        doc = db.pdf_texts.find_one({"user_id": user_id})
        return str(doc["_id"]) if doc else None

def get_user_qa(user_id: str):
    data = db.user_qas.find_one({"user_id": user_id})
    return data
def get_user_PDF(user_id: str):
    data = db.pdf_texts.find_one({"user_id": user_id})
    return data

# New: Update answer for a question index and return next question (if any)

def update_answer_and_get_next(user_id: str,pdf_id: str, question_index: int, answer: str):
    print(f"Updating answer for question {user_id} to {pdf_id}")
    user_qa = db.user_qas.find_one({"user_id": user_id,"pdf_id":pdf_id})
    
    # Convert user_qa to JSON if it's a string
    if isinstance(user_qa, str):
        try:
            user_qa = json.loads(user_qa)
            print("Successfully converted user_qa string to JSON")
        except json.JSONDecodeError as e:
            print(f"Error converting user_qa to JSON: {str(e)}")
            return None, None
    user_qa= user_qa["user_qa"]['qas']
    print(f"User QA: {user_qa}")

    if not user_qa or question_index >= len(user_qa):
        print("No user_qa or qas found")
        return None, None
    # Update answer
    qas = user_qa
    qas[question_index]["answer"] = answer
    print(f"Updating answer for question {question_index} to {answer}")
    db.user_qas.update_one(
        {"user_id": user_id,"pdf_id":pdf_id},
        {"$set": {f"user_qa.qas.{question_index}.answer": answer}}
    )
    # Find next unanswered question
    for idx, qa in enumerate(qas):
        if not qa.get("answer"):
            print(f"Found next unanswered question {idx}")
            return idx, qa["question"]
    return None, None  # All answered 