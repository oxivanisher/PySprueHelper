from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw
import pytesseract
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Mocked admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password'

# Mock project storage
projects = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Index route (login or redirect to projects)
@app.route('/')
def index():
    if 'logged_in' in session:
        return redirect(url_for('projects'))
    return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('projects'))
        else:
            flash('Invalid credentials')

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Project management page
# Mock project storage (rename from projects to project_db)
project_db = {}

@app.route('/projects', methods=['GET', 'POST'])
def projects():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        project_name = request.form['project_name']
        if project_name and project_name not in project_db:
            project_db[project_name] = []
        return redirect(url_for('upload_sprue', project_name=project_name))

    return render_template('projects.html', project_list=project_db)


# Upload sprue images to a project
@app.route('/upload/<project_name>', methods=['GET', 'POST'])
def upload_sprue(project_name):
    if 'logged_in' not in session:
        return redirect(url_for('login'))

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
            project_db[project_name].append(highlighted_image_path)

            return redirect(url_for('view_sprue', filename=highlighted_image_path))

    return render_template('upload.html', project_name=project_name)

# Highlight numbers using OCR
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

# View sprue image
@app.route('/view_sprue/<filename>')
def view_sprue(filename):
    return render_template('view_sprue.html', filename=filename, numbers=[])

# Serve the highlighted images
@app.route('/uploads/<filename>')
def view_highlighted_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
