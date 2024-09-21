
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
import pytesseract
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_sprue():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)
            
            highlighted_image_path = highlight_numbers(image_path)
            
            return redirect(url_for('view_sprue', filename=highlighted_image_path))
    
    return render_template('upload.html')

def highlight_numbers(image_path):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    ocr_result = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    
    for i in range(len(ocr_result['text'])):
        text = ocr_result['text'][i]
        if text.strip() and text.isdigit():
            x, y, w, h = ocr_result['left'][i], ocr_result['top'][i], ocr_result['width'][i], ocr_result['height'][i]
            draw.rectangle([x, y, x + w, y + h], outline="red", width=2)
            draw.text((x, y - 10), text, fill="red")
    
    highlighted_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'highlighted_' + os.path.basename(image_path))
    image.save(highlighted_image_path)
    return highlighted_image_path

@app.route('/view_sprue/<filename>')
def view_sprue(filename):
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    ocr_result = pytesseract.image_to_data(Image.open(image_path), output_type=pytesseract.Output.DICT)
    
    detected_numbers = []
    for i in range(len(ocr_result['text'])):
        text = ocr_result['text'][i]
        if text.strip() and text.isdigit():
            detected_numbers.append({
                'text': text,
                'x': ocr_result['left'][i],
                'y': ocr_result['top'][i],
                'width': ocr_result['width'][i],
                'height': ocr_result['height'][i]
            })
    
    return render_template('view_sprue.html', filename=filename, numbers=detected_numbers)

@app.route('/uploads/<filename>')
def view_highlighted_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
