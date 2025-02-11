import os
import PyPDF2
import img2pdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def merge_pdf_files(files):
    merger = PyPDF2.PdfMerger()
    for file in files:
        merger.append(file)
    
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'merged.pdf')
    merger.write(output_path)
    merger.close()
    return output_path

def convert_image_to_pdf(image_path):
    pdf_path = image_path.rsplit('.', 1)[0] + '_temp.pdf'
    img = Image.open(image_path)
    img.convert('RGB').save(pdf_path, 'PDF')
    return pdf_path

def convert_other_file_to_pdf(file_path):
    try:
        # Try converting with img2pdf first
        import img2pdf
        with open(file_path, 'rb') as file:
            pdf_bytes = img2pdf.convert(file)
            pdf_path = file_path.rsplit('.', 1)[0] + '_temp.pdf'
            with open(pdf_path, 'wb') as pdf_file:
                pdf_file.write(pdf_bytes)
            return pdf_path
    except ImportError:
        # Fallback to reportlab if img2pdf is not available
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        pdf_path = file_path.rsplit('.', 1)[0] + '_temp.pdf'
        c = canvas.Canvas(pdf_path, pagesize=letter)
        width, height = letter
        
        # Add file content to PDF (basic conversion)
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
            text_object = c.beginText(100, height - 100)
            text_object.setFont("Helvetica", 12)
            
            # Split text into lines
            for line in text.split('\n'):
                text_object.textLine(line)
            
            c.drawText(text_object)
            c.showPage()
            c.save()
        
        return pdf_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge', methods=['POST'])
def merge():
    if 'files' not in request.files:
        return 'No file part', 400
    
    files = request.files.getlist('files')
    
    # Get custom filename from form data, default to 'merged' if not provided
    custom_filename = request.form.get('filename', 'merged').strip()
    
    # Sanitize filename to remove any potentially dangerous characters
    custom_filename = ''.join(c for c in custom_filename if c.isalnum() or c in (' ', '_', '-'))
    
    # Ensure filename ends with .pdf
    if not custom_filename.lower().endswith('.pdf'):
        custom_filename += '.pdf'
    
    # Save uploaded files
    saved_files = []
    for file in files:
        if file.filename == '':
            continue
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        saved_files.append(filepath)
    
    if not saved_files:
        return 'No files uploaded', 400
    
    merged_pdf = merge_pdf_files(saved_files)
    
    # Rename the merged PDF to the custom filename
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], custom_filename)
    os.rename(merged_pdf, output_path)
    
    # Clean up temporary files
    for file in saved_files:
        os.remove(file)
    
    return send_file(output_path, as_attachment=True, download_name=custom_filename)

if __name__ == '__main__':
    app.run(debug=True)
