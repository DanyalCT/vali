# question.py
from pydantic import BaseModel, Field
from typing import List, Optional

class QAItem(BaseModel):
    question: str
    answer: Optional[str] = None

class UserQA(BaseModel):
    user_id: str = Field(..., description="MongoDB user id")
    qas: List[QAItem]

class AnswerRequest(BaseModel):
    user_id: str
    question_index: int
    answer: str 