# server.py

import os
import time
import asyncio
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel

from solver.quiz_solver import solve_quiz_chain

EXPECTED_SECRET = os.getenv("QUIZ_SECRET")
if not EXPECTED_SECRET:
    raise RuntimeError("QUIZ_SECRET is required in environment")

app = FastAPI(title="LLM Quiz Solver Service")


class QuizPayload(BaseModel):
    email: str
    secret: str
    url: str


@app.post("/", status_code=200)
async def main_handler(payload: QuizPayload, request: Request):
    if payload.secret != EXPECTED_SECRET:
        raise HTTPException(status_code=403, detail="invalid secret")

    start_time = time.time()
    try:
        result = await asyncio.wait_for(
            solve_quiz_chain(
                payload.email,
                payload.secret,
                payload.url,
                start_time,
                max_seconds=180
            ),
            timeout=180
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=500, 
            detail="Processing timed out (over 3 minutes)"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error computing answer: {e}"
        )

    return {"ok": True, "result": result}
