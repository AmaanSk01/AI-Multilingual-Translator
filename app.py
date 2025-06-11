from flask import Flask, render_template, request, send_file, jsonify
import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from docx import Document
from googletrans import Translator

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Configure Poppler Path 
POPPLER_PATH = r"C:\Users\amaan\Downloads\Release-24.08.0-0.zip"

# Function to extract text from PDFs
def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text

# Function to extract text from images
def extract_text_from_image(image_path):
    return pytesseract.image_to_string(Image.open(image_path))

# Function to extract text from Word Documents (.docx)
def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Function to translate text
def translate_text(text, target_lang):
    translator = Translator()
    translated = translator.translate(text, dest=target_lang)
    return translated.text

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/translate", methods=["POST"])
def translate():
    # Check if user provided manual input
    manual_text = request.form.get("manual_text")
    target_lang = request.form.get("language", "en")

    if manual_text:  # If user entered text manually
        translated_text = translate_text(manual_text, target_lang)
        return jsonify({"text": translated_text})

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"})

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
# Detect file type and extract text
    if file.filename.endswith(".pdf"):
        extracted_text = extract_text_from_pdf(file_path)
    elif file.filename.endswith(".docx"):
        extracted_text = extract_text_from_docx(file_path)
    elif file.filename.endswith((".png", ".jpg", ".jpeg")):
        extracted_text = extract_text_from_image(file_path)
    else:
        return jsonify({"error": "Unsupported file format"})
    
    # Translate extracted text
    translated_text = translate_text(extracted_text, target_lang)

    # Save translated text to a file
    translated_file_path = os.path.join(UPLOAD_FOLDER, "translated.txt")
    with open(translated_file_path, "w", encoding="utf-8") as f:
        f.write(translated_text)

    return jsonify({"text": translated_text, "download_url": "/download"})

@app.route("/download")
def download():
    return send_file(os.path.join(UPLOAD_FOLDER, "translated.txt"), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)