# solver/llm_agent.py
import os
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

deepseek_client = None
openai_client = None

if DEEPSEEK_API_KEY:
    try:
        from deepseek import DeepSeekAPI
        deepseek_client = DeepSeekAPI(api_key=DEEPSEEK_API_KEY)
    except Exception:
        deepseek_client = None

if not deepseek_client and OPENAI_API_KEY:
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        openai_client = openai
    except Exception:
        openai_client = None

def _extract_json_block(s: str):
    s = (s or "").strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    start = None
    for i, ch in enumerate(s):
        if ch in "{[":
            start = i
            break
    if start is None:
        raise ValueError("No JSON found")
    stack = []
    for i in range(start, len(s)):
        ch = s[i]
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if not stack:
                continue
            stack.pop()
            if not stack:
                return json.loads(s[start:i+1])
    raise ValueError("Could not parse JSON block")

async def _call_deepseek(prompt: str):
    loop = asyncio.get_running_loop()
    def fn():
        # Try multiple possible SDK shapes
        if hasattr(deepseek_client, "completions"):
            resp = deepseek_client.completions.create(
                model="deepseek-chat",
                messages=[{"role":"user","content":prompt}]
            )
            choice = resp.choices[0]
            if hasattr(choice, "message"):
                return getattr(choice.message, "content", "") or ""
            return choice.get("text","") or ""
        if hasattr(deepseek_client, "ask"):
            resp = deepseek_client.ask(prompt)
            return resp.get("text") or str(resp)
        return str(deepseek_client)
    return await loop.run_in_executor(None, fn)

async def _call_openai(prompt: str):
    loop = asyncio.get_running_loop()
    def fn():
        resp = openai_client.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )
        return resp.choices[0].message.content
    return await loop.run_in_executor(None, fn)

async def ask_llm(prompt: str) -> str:
    if deepseek_client:
        return await _call_deepseek(prompt)
    if openai_client:
        return await _call_openai(prompt)
    raise RuntimeError("No LLM configured (set DEEPSEEK_API_KEY or OPENAI_API_KEY)")

async def ask_llm_json(prompt: str, retries:int=2) -> dict:
    raw = await ask_llm(prompt)
    for _ in range(retries+1):
        try:
            return _extract_json_block(raw)
        except Exception:
            coax = f"You must output only valid JSON now. Previous response:\n{raw}\n\nNow reply with valid JSON only."
            raw = await ask_llm(coax)
    raise ValueError("Failed to parse JSON from LLM")
