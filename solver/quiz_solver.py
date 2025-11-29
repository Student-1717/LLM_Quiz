# solver/quiz_solver.py
import time
import json
import re
from pathlib import Path
from solver.browser import render_page
from solver.llm_agent import ask_llm_json, ask_llm
from utils.fetch import download_file
from utils.pdf_tools import extract_text_from_pdf, extract_tables_from_pdf
import aiohttp

MAX_PAYLOAD_BYTES = 900_000

def _find_submit_url(html: str, text: str):
    m = re.search(r'(https?://[^\s\'"<>]+/submit[^\s\'"<>]*)', (html or "") + "\n" + (text or ""))
    return m.group(1) if m else None

async def _prepare_files_for_llm(paths):
    out = []
    for p in paths:
        p = str(p)
        if p.lower().endswith(".pdf"):
            txt = extract_text_from_pdf(p)
            out.append(f"FILE {p} (pdf excerpt):\n{txt[:4000]}")
        elif p.lower().endswith(".csv") or p.lower().endswith(".tsv"):
            try:
                import pandas as pd
                df = pd.read_csv(p)
                out.append(f"FILE {p} (csv sample):\n{df.head(20).to_csv(index=False)}")
            except Exception:
                out.append(f"FILE {p} (csv unreadable)")
        else:
            try:
                txt = Path(p).read_text(encoding="utf-8", errors="ignore")
                out.append(f"FILE {p} (text excerpt):\n{txt[:4000]}")
            except Exception:
                out.append(f"FILE {p} (binary or unreadable)")
    return out

async def _post_answer(submit_url: str, payload: dict, timeout:int=30):
    async with aiohttp.ClientSession() as session:
        async with session.post(submit_url, json=payload, timeout=timeout) as resp:
            try:
                return await resp.json()
            except Exception:
                return {"status": resp.status, "text": await resp.text()}

async def solve_quiz_chain(email: str, secret: str, start_url: str, start_time: float, max_seconds: int = 180):
    steps = []
    url = start_url
    while True:
        elapsed = time.time() - start_time
        if elapsed > max_seconds:
            steps.append({"url": url, "error": "timeout"})
            break

        try:
            html, text = await render_page(url)
        except Exception as e:
            steps.append({"url": url, "error": f"render_failed: {e}"})
            break

        steps.append({"url": url, "page_text_len": len(text or "")})

        plan_prompt = f"""
You are an automated agent. Output ONLY valid JSON with fields:
- needs_download: list of file URLs to download (or empty)
- answer: the value to submit (number/string/boolean/object)
- submit_url: optional (otherwise the page contains the submit URL)

PAGE_TEXT:
{text}

PAGE_HTML:
{html}
"""
        try:
            parsed = await ask_llm_json(plan_prompt)
        except Exception:
            try:
                raw = await ask_llm(plan_prompt)
                parsed = json.loads(raw)
            except Exception as e:
                steps.append({"url": url, "error": f"llm_parse_failed: {e}"})
                break

        needs = parsed.get("needs_download", []) or []
        answer_value = parsed.get("answer")
        submit_url = parsed.get("submit_url") or _find_submit_url(html, text)

        downloaded_paths = []
        if needs:
            for fu in needs:
                try:
                    p = await download_file(fu)
                    downloaded_paths.append(p)
                except Exception as e:
                    steps.append({"url": url, "error": f"download_failed {fu}: {e}"})

            files_for_llm = await _prepare_files_for_llm(downloaded_paths)
            second_prompt = f"""
Use the following downloaded file contents and page text to compute the final answer.
FILES:
{chr(10).join(files_for_llm)}

PAGE_TEXT:
{text}

Return only valid JSON: {{ "answer": <value> }}
"""
            try:
                parsed2 = await ask_llm_json(second_prompt)
                answer_value = parsed2.get("answer")
            except Exception:
                raw2 = await ask_llm(second_prompt)
                try:
                    parsed2 = json.loads(raw2)
                    answer_value = parsed2.get("answer")
                except Exception:
                    answer_value = raw2

        payload = {"email": email, "secret": secret, "url": url, "answer": answer_value}
        import json as _j
        if len(_j.dumps(payload).encode("utf-8")) > MAX_PAYLOAD_BYTES:
            if isinstance(answer_value, str) and len(answer_value) > 2000:
                payload["answer"] = answer_value[:1800] + "...[truncated]"
            else:
                payload["answer"] = str(answer_value)[:1800]
            if len(_j.dumps(payload).encode("utf-8")) > MAX_PAYLOAD_BYTES:
                steps.append({"url": url, "error": "payload_too_large"})
                break

        if not submit_url:
            steps.append({"url": url, "answer_payload": payload, "submit_url": None})
            break

        try:
            resp = await _post_answer(submit_url, payload)
            steps.append({"url": url, "submit_url": submit_url, "submit_response": resp})
        except Exception as e:
            steps.append({"url": url, "submit_error": str(e)})
            break

        next_url = None
        if isinstance(resp, dict):
            next_url = resp.get("url")
            correct = resp.get("correct")
            if correct is False and not next_url:
                re_prompt = f"""
Previous submission was incorrect. Using the same page content below, produce a corrected answer JSON.
PAGE_TEXT:
{text}
PAGE_HTML:
{html}
Return only: {{ "answer": <value> }}
"""
                try:
                    retry_parsed = await ask_llm_json(re_prompt)
                    payload["answer"] = retry_parsed.get("answer")
                    resp2 = await _post_answer(submit_url, payload)
                    steps.append({"url": url, "resubmit_response": resp2})
                    if isinstance(resp2, dict) and resp2.get("url"):
                        next_url = resp2.get("url")
                except Exception:
                    pass

        if not next_url:
            break

        url = next_url

    return {"steps": steps}
