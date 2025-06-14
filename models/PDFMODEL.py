# question.py
from pydantic import BaseModel, Field
from typing import List, Optional

class PDFFORMAT(BaseModel):
    user_id: str = Field(..., description="MongoDB user id")
    pdf_text: Optional[str] = Field(None, description="Extracted text from the PDF document")
