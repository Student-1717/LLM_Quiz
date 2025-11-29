# utils/pdf_tools.py
import pdfplumber
import pandas as pd

def extract_text_from_pdf(path: str) -> str:
    out = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            out.append(page.extract_text() or "")
    return "\n".join(out)

def extract_tables_from_pdf(path: str):
    tables = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                try:
                    df = pd.DataFrame(table[1:], columns=table[0])
                except Exception:
                    df = pd.DataFrame(table)
                tables.append(df)
    return tables
