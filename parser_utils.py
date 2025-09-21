# parser_utils.py
import fitz  # PyMuPDF
import docx
import re

def extract_text_from_pdf_bytes(file_bytes):
    """
    file_bytes: bytes-like (uploaded_file.read())
    returns: string text
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = []
        for page in doc:
            text.append(page.get_text())
        return "\n".join(text)
    except Exception:
        return ""

def extract_text_from_docx_bytes(file_bytes):
    """
    file_bytes: bytes-like (uploaded_file.read())
    docx.Document can accept a file-like object if wrapped
    """
    try:
        # docx expects a path or a file-like object. We'll decode bytes via BytesIO
        from io import BytesIO
        f = BytesIO(file_bytes)
        doc = docx.Document(f)
        paras = [p.text for p in doc.paragraphs]
        return "\n".join(paras)
    except Exception:
        return ""

def clean_text(text):
    if not text:
        return ""
    # Normalize whitespace and lower
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_uploaded_file(uploaded_file):
    """
    uploaded_file: streamlit uploaded file
    return: parsed plain text (lowercased, cleaned)
    """
    if uploaded_file is None:
        return ""
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    if name.endswith(".pdf"):
        txt = extract_text_from_pdf_bytes(raw)
    elif name.endswith(".docx") or name.endswith(".doc"):
        txt = extract_text_from_docx_bytes(raw)
    else:
        try:
            txt = raw.decode("utf-8", errors="ignore")
        except Exception:
            txt = ""
    return clean_text(txt).lower()
