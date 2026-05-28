from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, field_validator
from typing import List
import google.generativeai as genai
from dotenv import load_dotenv
import os
import logging

# ── Setup ─────────────────────────────────────────────────────────────────────
load_dotenv()
print("key", os.getenv("GEMINI_API_KEY"))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Load resume context once at startup
with open("resume_context.md", "r") as f:
    resume_context = f.read()

SYSTEM_PROMPT = f"""You are a helpful assistant representing Mickael Maujean on his personal resume website.
Answer questions about his background, skills, work experience, projects, and education based on the resume below.
Be concise, friendly, and professional. Keep answers short (5 sentences max).
If asked something not covered in the resume, politely say you don't have that information and guide the user to the contact section
Never invent or assume details not present in the resume.
Do not answer questions unrelated to Mickael's professional profile.

--- RESUME ---
{resume_context}
"""

# ── Rate limiter ───────────────────────────────────────────────────────────────
# Limits are per IP address:
#   - 10 requests/minute  → prevents burst abuse
#   - 100 requests/day    → prevents sustained abuse draining your free quota
limiter = Limiter(key_func=get_remote_address, default_limits=["100/day", "10/minute"])

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(title="Resume Chatbot API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# ── Models ─────────────────────────────────────────────────────────────────────
class Message(BaseModel):
    role: str   # "user" or "model"
    content: str

    @field_validator("role")
    @classmethod
    def role_must_be_valid(cls, v):
        if v not in ("user", "model"):
            raise ValueError("role must be 'user' or 'model'")
        return v

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("content cannot be empty")
        if len(v) > 1000:
            raise ValueError("message too long (max 1000 characters)")
        return v.strip()

class ChatRequest(BaseModel):
    messages: List[Message]

    @field_validator("messages")
    @classmethod
    def messages_not_empty(cls, v):
        if not v:
            raise ValueError("messages list cannot be empty")
        if len(v) > 20:
            raise ValueError("too many messages in history (max 20)")
        return v

# ── Gemini model ───────────────────────────────────────────────────────────────
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config={
        "max_output_tokens": 300,   # Keep replies short → saves tokens
        "temperature": 0.7,
    },
)

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message" : "Resume Chatbot API is running. Use POST /chat to interact"}

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, body: ChatRequest):
    try:
        # Build Gemini history from all messages except the last (that's the new user input)
        history = [
            {"role": m.role, "parts": [m.content]}
            for m in body.messages[:-1]
        ]

        last_message = body.messages[-1].content
        logger.info(f"New chat request | IP: {get_remote_address(request)} | msg: {last_message[:60]}")

        chat_session = model.start_chat(history=history)

        # Prepend system prompt to the first user message if no history,
        # otherwise just send the user message
        if not history:
            prompt = f"{SYSTEM_PROMPT}\n\nUser: {last_message}"
        else:
            prompt = last_message

        response = chat_session.send_message(prompt)
        return {"reply": response.text}

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise HTTPException(status_code=502, detail="AI service unavailable. Please try again later.")
