import os
import re

from flask import Flask, render_template, request, jsonify
from PyPDF2 import PdfReader

import google.generativeai as genai

# OCR related
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image


# ================== PATH CONFIG ==================

# Path to Tesseract EXE (change if installed elsewhere)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Path to Poppler bin folder (change if you extracted Poppler somewhere else)
POPPLER_PATH = r"C:\poppler\Library\bin"  # <- update this if needed


# ================== AI TEXT CLEANER ==================

def clean_ai_text(raw: str) -> str:
    """Clean markdown, emojis, and turn bullets into smooth paragraphs."""
    if not raw:
        return ""

    # Remove basic markdown symbols
    txt = (
        raw.replace("**", "")
           .replace("*", "")
           .replace("_", "")
           .replace("###", "")
           .replace("##", "")
           .replace("#", "")
    )

    # Remove most emojis / non-ASCII chars
    txt = "".join(ch for ch in txt if ord(ch) < 128)

    # Split lines, strip bullet markers and join nicely
    lines = []
    for line in txt.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")  # keep paragraph breaks
            continue

        # remove bullet prefixes like "- ", "• ", "1. ", "2) " etc.
        stripped = re.sub(r"^[-\u2022*]\s+", "", stripped)      # - , • , *
        stripped = re.sub(r"^\d+[\.\)]\s+", "", stripped)       # 1.  2) ...

        lines.append(stripped)

    # Rebuild paragraphs
    paragraphs = []
    current = []
    for line in lines:
        if line == "":
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append(" ".join(current))

    return "\n\n".join(paragraphs).strip()


# ================== FLASK + GEMINI SETUP ==================

app = Flask(__name__)

# Try env var first
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

# Fallback: direct key in code (local only – do NOT upload to GitHub)
if not GEMINI_KEY:
    GEMINI_KEY = "AIzaSyB668g2x1jVvPMMFCnRClEXMKTLz4XALCA"  # <- your key

genai.configure(api_key=GEMINI_KEY)


# ================== TEXT EXTRACTION HELPERS ==================

def extract_text_from_pdf(file_storage, max_pages=None):
    """
    Extract text from PDF.
    1) Try normal text extraction (for digital PDFs).
    2) If nothing extracted, fallback to OCR using pdf2image + Tesseract.
    """
    reader = PdfReader(file_storage)
    text_chunks = []

    # --- normal extraction ---
    for i, page in enumerate(reader.pages):
        if max_pages is not None and i >= max_pages:
            break
        page_text = page.extract_text()
        if page_text:
            text_chunks.append(page_text)

    extracted_text = "\n\n".join(text_chunks).strip()

    # --- OCR fallback ---
    if not extracted_text:
        print(">>> Using OCR mode for PDF…")

        file_storage.seek(0)
        images = convert_from_bytes(
            file_storage.read(),
            poppler_path=POPPLER_PATH
        )

        ocr_text = []
        for img in images:
            text = pytesseract.image_to_string(img)
            if text.strip():
                ocr_text.append(text)

        if ocr_text:
            return "\n\n".join(ocr_text)

        return ""

    return extracted_text


def extract_text_from_image(file_storage):
    """Extract text from JPG/PNG using OCR."""
    try:
        img = Image.open(file_storage.stream)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        print("Image OCR error:", e)
        return ""


# ================== ROUTES ==================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/extract", methods=["POST"])
def extract():
    """
    Takes a PDF or image upload and returns extracted text as JSON.
    Accepts: PDF, JPG, PNG.
    """
    # handle both old name "pdf" and new "fileInput"
    uploaded = None
    if "fileInput" in request.files:
        uploaded = request.files["fileInput"]
    elif "pdf" in request.files:
        uploaded = request.files["pdf"]

    if not uploaded:
        return jsonify({"error": "No file uploaded"}), 400

    if uploaded.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filename = uploaded.filename.lower()

    try:
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(uploaded, max_pages=None)
        elif filename.endswith((".jpg", ".jpeg", ".png")):
            text = extract_text_from_image(uploaded)
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        if not text or not text.strip():
            return jsonify({"error": "Could not extract text from this file"}), 400

        return jsonify({"success": True, "text": text})
    except Exception as e:
        return jsonify({"error": f"Error processing file: {e}"}), 500


@app.route("/teach", methods=["POST"])
def teach():
    """
    AI Teacher endpoint:
      - context: full extracted text
      - selected: optional selected part (topic/question)
      - question: optional doubt typed by user
    Returns: teacher-style explanation / answers.
    """
    data = request.get_json(force=True)
    context = (data.get("context") or "").strip()
    selected = (data.get("selected") or "").strip()
    question = (data.get("question") or "").strip()

    if not context:
        return jsonify({"error": "No document content provided"}), 400

    # Limit context size so we don’t overload the model
    max_chars = 12000
    context = context[:max_chars]

    # ---------- Instruction for the AI teacher ----------
    if not question and selected:
        user_instruction = (
            "You are explaining ONLY the selected part to 1st/2nd year CSE students. "
            "Start the answer with 'Alright students,' then explain in simple "
            "paragraphs. After the explanation, give an 'Exam points:' section "
            "with 3–6 short points they can write in the exam. "
            "Do NOT use markdown, bullets, emojis or parentheses."
        )
    elif question:
        user_instruction = (
            f"You are answering this exam-style question using ONLY the document content "
            f"if possible:\n\"{question}\".\n"
            "Start with 'Alright students,' and then give a clear explanation in "
            "paragraph form. After that, add an 'Exam points:' section with "
            "3–6 short, direct points. Do NOT use markdown, bullets, emojis or "
            "parentheses. Just plain text."
        )
    else:
        user_instruction = (
            "You are summarizing the main ideas of this document for 1st/2nd year CSE "
            "students. Start with 'Alright students,' then explain topic-wise in "
            "simple paragraphs. After the explanation, add an 'Exam points:' "
            "section with 3–8 short points. Do NOT use markdown, bullets, emojis "
            "or parentheses. Just plain text."
        )

    prompt = f"""
PDF OR IMAGE TEXT CONTENT:
\"\"\"{context}\"\"\"

SELECTED PART (may be empty):
\"\"\"{selected}\"\"\"

INSTRUCTION:
{user_instruction}
"""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)

        raw = (response.text or "").strip()
        answer = clean_ai_text(raw)

        if not answer:
            answer = (
                "Alright students, I could not find enough information in this "
                "document to answer clearly."
            )

        return jsonify({"success": True, "answer": answer})

    except Exception as e:
        return jsonify({"error": f"Gemini AI Teacher error: {e}"}), 500


# ================== MAIN ==================

if __name__ == "__main__":
    app.run(debug=True)
