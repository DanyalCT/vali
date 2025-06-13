# Valoov AI Backend

A FastAPI backend for generating and managing question-answer pairs from PDF documents using Google Gemini LLM and MongoDB.

## Project Structure

- `core/` — Core logic (PDF extraction, LLM integration, config)
- `db/` — Database connection and CRUD operations
- `models/` — Pydantic models for API and database
- `main.py` — FastAPI app entry point

## Setup Instructions

1. **Clone the repository**

```bash
git clone <repo-url>
cd Valoov_AI_Backend
```

2. **Install dependencies** (using [uv](https://docs.astral.sh/uv/getting-started/))

```bash
uv sync
```

3. **Set up environment variables**

Create a `.env` file in the root directory with the following:

```
MONGODB_URI=mongodb://localhost:27017
GEMINI_API_KEY=your-gemini-api-key
```

4. **Run the API server**

```bash
uv run uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

### 1. Generate Questions from PDF

**POST** `/api/v1/questions/generate`

- **Form Data:**
  - `user_id` (string): Unique user identifier
  - `pdf` (file): PDF document to upload

**Response:**
```
{
  "user_id": "...",
  "question_index": 0,
  "question": "First generated question"
}
```

### 2. Submit Answer and Get Next Question

**POST** `/api/v1/questions/answer`

- **JSON Body:**
```
{
  "user_id": "...",
  "question_index": 0,
  "answer": "Your answer here"
}
```

**Response:**
- If more questions remain:
```
{
  "user_id": "...",
  "question_index": 1,
  "question": "Next question"
}
```
- If all questions are answered:
```
{
  "user_id": "...",
  "message": "All questions answered!"
}
```

## Testing the API with Postman

### 1. Generate Questions
- Set method to `POST` and URL to `http://127.0.0.1:8000/api/v1/questions/generate`
- In the `Body` tab, select `form-data`
  - Add a `user_id` field (type: text)
  - Add a `pdf` field (type: file) and upload your PDF
- Click `Send`
- You will receive the first question in the response

### 2. Answer a Question
- Set method to `POST` and URL to `http://127.0.0.1:8000/api/v1/questions/answer`
- In the `Body` tab, select `raw` and choose `JSON`
- Enter:
```
{
  "user_id": "your_user_id",
  "question_index": 0,
  "answer": "Your answer here"
}
```
- Click `Send`
- You will receive the next question or a completion message

## Environment Variables
- `MONGODB_URI`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `GEMINI_API_KEY`: Google Gemini API key for LLM

---

**Tip:** You can also explore the API docs at `http://127.0.0.1:8000/docs` when the server is running.
