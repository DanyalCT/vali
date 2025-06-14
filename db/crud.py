# crud.py
from db.mongodb import db
from models.question import UserQA
from models.PDFMODEL import PDFFORMAT

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
def update_answer_and_get_next(user_id: str, question_index: int, answer: str):
    user_qa = db.user_qas.find_one({"user_id": user_id})
    if not user_qa or "qas" not in user_qa or question_index >= len(user_qa["qas"]):
        return None, None
    # Update answer
    qas = user_qa["qas"]
    qas[question_index]["answer"] = answer
    db.user_qas.update_one(
        {"user_id": user_id},
        {"$set": {f"qas.{question_index}.answer": answer}}
    )
    # Find next unanswered question
    for idx, qa in enumerate(qas):
        if not qa.get("answer"):
            return idx, qa["question"]
    return None, None  # All answered 