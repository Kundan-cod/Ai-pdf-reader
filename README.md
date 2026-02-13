# 📚 AI PDF Reader & Study Teacher

An intelligent web application that helps you read, understand, and study PDF documents. It combines OCR for text extraction, Text-to-Speech for auditory learning, and Google's Gemini AI to act as a personal tutor.

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.x-green.svg)

## ✨ Features

- **📄 Document Support**: Handles standard PDFs and scanned images/PDFs (using OCR).
- **🔊 Text-to-Speech**: Read documents aloud with customizable voice, speed, and pitch.
- **👨‍🏫 AI Teacher**: 
  - Explains complex topics in simple terms.
  - Answers specific questions from the document.
  - Generates exam-style points for quick revision.
- **📖 Smart Reading Modes**:
  - **Read All**: Reads the entire document continuously.
  - **Topic-wise Read**: Automatically detects headings and reads section by section.
  - **Selected Text**: Reads only what you highly.

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **AI Model**: Google Gemini 1.5 Flash (via `google-generativeai`)
- **PDF Processing**: `PyPDF2`, `pdf2image`, `pytesseract` (Tesseract-OCR)

## 🚀 Setup & Installation

### Prerequisites
- Python 3.8+
- [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed on your system.
- [Poppler](http://blog.alivate.com.au/poppler-windows/) installed (for PDF to image conversion).

### 1. Clone the Repository
```bash
git clone https://github.com/Kundan-cod/Ai-pdf-reader.git
cd Ai-pdf-reader
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Key
You can set your Google Gemini API key in `app.py` or use an environment variable.

**Option A: Environment Variable (Recommended)**
```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="your_api_key_here"

# Windows (CMD)
set GEMINI_API_KEY=your_api_key_here
```

**Option B: Direct Update**
Update the `GEMINI_KEY` variable in `app.py`.

### 4. Run the Application
```bash
python app.py
```
Access the app at `http://127.0.0.1:5000`

## 📝 Usage Guide

1. **Upload**: Click "Choose a PDF file" and hit "Extract Text".
2. **Listen**: Use the controls on the left to change voice/speed and click "Read All".
3. **Learn**: 
   - Select a confusing paragraph and click "Ask AI Teacher".
   - Or type a specific question in the box to get an answer based on the PDF content.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📄 License

This project is licensed under the MIT License.