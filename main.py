#main.py
from fastapi import FastAPI, UploadFile, File, Form, Body
from core.pdf_utils import extract_text_from_pdf
from core.llm import generate_questions_from_text
from db.crud import save_user_qa, update_answer_and_get_next
from models.question import UserQA, QAItem, AnswerRequest
import io
from core.startup_valuation import perform_startup_valuation
from core.generate_report_llm import generate_report
from core.fetch_data_by_id import fetch_data_by_id
from core.FCFFprojection import perform_fcff_projection
from bson import ObjectId
from db.crud import save_pdf_text
from pydantic import BaseModel

class FCFFRequest(BaseModel):
    pdf_id: str
    userMSG: str

class ValuationRequest(BaseModel):
    pdf_id: str

app = FastAPI()

@app.post("/api/v1/valuation")
async def valuation(request: ValuationRequest):
    result = perform_startup_valuation(request.pdf_id)
    return {"result": result}

@app.post("/api/v1/questions/generate")
async def generate_questions(user_id: str = Form(...), pdf: UploadFile = File(...)):
    pdf_bytes = await pdf.read()
    text = extract_text_from_pdf(io.BytesIO(pdf_bytes))
    
    # Save pdf_text separately
    pdf_id = save_pdf_text(user_id, text)

    # Continue with QA flow
    questions = generate_questions_from_text(text)
    qa_items = [QAItem(question=q) for q in questions]
    user_qa = UserQA(user_id=user_id, qas=qa_items)
    save_user_qa(user_qa,pdf_id)

    return {"user_id": user_id, "pdf_id": pdf_id, "question_index": 0, "question": questions[0] if questions else None}

@app.post("/api/v1/questions/answer")
async def answer_question(req: AnswerRequest):
    next_index, next_question = update_answer_and_get_next(req.user_id,req.pdf_id, req.question_index, req.answer)
    if next_question is not None:
        return {"user_id": req.user_id, "question_index": next_index, "question": next_question,"pdf_id": req.pdf_id,"all_questions_answered": False}
    else:
        return {"user_id": req.user_id,"pdf_id": req.pdf_id,"all_questions_answered": True, "message": "All questions answered!"}
    
@app.get("/generate-report/{doc_id}")
def generate_llm_report(doc_id: str):
    eval_text, pdf_text = fetch_data_by_id(ObjectId(doc_id))
    if not eval_text or not pdf_text:
        return {"error": "Missing data in document"}
    
    report = generate_report(eval_text, pdf_text)
    return {"report": report}

@app.post("/api/v1/fcff-projection/")
async def get_fcff_projection(request: FCFFRequest):
    """
    Get FCFF projection for a given PDF ID.
    
    Args:
        request (FCFFRequest): Request body containing pdf_id and userMSG
        
    Returns:
        dict: FCFF projection results including the formatted table
    """
    try:
        result = perform_fcff_projection(request.pdf_id, request.userMSG)
        if "error" in result:
            return {"error": result["error"]}
        return result
    except Exception as e:
        return {"error": f"Error processing FCFF projection: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
