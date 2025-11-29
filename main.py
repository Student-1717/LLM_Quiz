import os
import asyncio
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from pyppeteer import launch
import aiohttp

load_dotenv()

EXPECTED_SECRET = os.getenv("QUIZ_SECRET")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

app = FastAPI()


# ------------------------------
# Pydantic payload model
# ------------------------------
class QuizPayload(BaseModel):
    email: str
    secret: str
    url: str
    class Config:
        extra = "allow"


# ------------------------------
# Render quiz page using Pyppeteer
# ------------------------------
async def render_page(url: str):
    browser = await launch(headless=True, args=["--no-sandbox"])
    page = await browser.newPage()

    await page.goto(url, {"waitUntil": "networkidle0"})

    html = await page.content()
    text = await page.evaluate("() => document.body.innerText")

    await browser.close()
    return html, text


# ------------------------------
# Call DeepSeek to compute answer
# ------------------------------
async def compute_answer(question_text: str):
    endpoint = "https://api.deepseek.com/v1/chat/completions"

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": f"Solve this quiz:\n\n{question_text}"}
        ]
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(endpoint, headers=headers, json=payload) as resp:
            data = await resp.json()

            try:
                return data["choices"][0]["message"]["content"].strip()
            except:
                return "Cannot compute"


# ------------------------------
# MAIN ENDPOINT
# ------------------------------
@app.post("/", status_code=200)
async def main_handler(payload: QuizPayload):

    # 1. Validate secret
    if payload.secret != EXPECTED_SECRET:
        raise HTTPException(status_code=403, detail="invalid secret")

    # 2. Render quiz page
    html, text = await render_page(payload.url)

    # 3. Compute answer using DeepSeek
    answer = await compute_answer(text)

    answer_obj = {
        "email": payload.email,
        "secret": payload.secret,
        "url": payload.url,
        "answer": answer
    }

    SUBMIT_URL = "https://tds-llm-analysis.s-anand.net/submit"

    # 4. Submit answer
    async with aiohttp.ClientSession() as session:
        async with session.post(SUBMIT_URL, json=answer_obj) as resp:
            try:
                submit_response = await resp.json()
            except:
                submit_response = {"status": resp.status, "text": await resp.text()}

    return {
        "ok": True,
        "submitted": True,
        "submit_url": SUBMIT_URL,
        "submit_response": submit_response
    }
