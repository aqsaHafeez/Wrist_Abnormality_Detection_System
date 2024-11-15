from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import sqlite3
import os
import subprocess
import sys
import glob
import logging
from flask import Flask, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'
# Flask-Mail configuration
# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'jazibsarwar9@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'axeg dqjo ktmo pfuj'  # Replace with your email password or app password
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        if not name or not email or not message:
            flash("Please fill out all fields.", "error")
            return redirect(url_for('index'))

        try:
            # Compose the email
            msg = Message(
                subject="New Contact Form Submission",
                sender=app.config['MAIL_USERNAME'],
                recipients=['jazibsarwar9@gmail.com'],  # Replace with the recipient email
                body=f"Name: {name}\nEmail: {email}\nMessage: {message}"
            )
            mail.send(msg)
            flash("Message sent successfully!", "success")
            return redirect(url_for('index'))
        except Exception as e:
            flash("Failed to send message. Please try again later.", "error")
            print(f"Error: {e}")

    return redirect(url_for('index'))


def get_db_connection():
    conn = sqlite3.connect('users.db')  
    conn.row_factory = sqlite3.Row
    return conn

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Initialize the database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT UNIQUE,
            username TEXT UNIQUE,
            password TEXT,
            question1 TEXT,
            question2 TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Directory paths for YOLOv9 detect script and processed images
YOLO_DETECT_SCRIPT = os.path.join('models', 'yolov9', 'detect.py')
YOLO_WEIGHTS = os.path.join('models', 'yolov9', 'best.pt')
DETECTED_IMAGE_PATH = os.path.join('static', 'diagnosed_image', 'latest_detection.jpg')
UPLOAD_IMAGE_PATH = os.path.join('static', 'uploaded_image.jpg')

@app.route('/')
def home():
    return redirect(url_for('login'))

import re
from flask import request, render_template, flash, redirect, url_for
import sqlite3

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['ConfirmPassword']
        question1 = request.form['question1']
        question2 = request.form['question2']

        # Email format validation using regex
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            flash("Invalid email format!", "error")
            return redirect(url_for('signup'))

        # Username validation: only letters and numbers, and not just numbers
        if not re.match("^[A-Za-z0-9]+$", username):
            flash("Username must contain only letters and numbers!", "error")
            return redirect(url_for('signup'))
        if username.isdigit():
            flash("Username cannot be just numbers!", "error")
            return redirect(url_for('signup'))

        # Password validation: Password and Confirm Password should match, and meet criteria
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('signup'))
        
        if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            flash("Password must be at least 8 characters long and contain both letters and numbers!", "error")
            return redirect(url_for('signup'))

        # Questions validation: they must not contain numbers
        if any(char.isdigit() for char in question1) or any(char.isdigit() for char in question2):
            flash("Security questions must not contain numbers!", "error")
            return redirect(url_for('signup'))

        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        # Check if email already exists
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        if c.fetchone():
            flash("Email already exists!", "error")
            conn.close()
            return redirect(url_for('signup'))

        # Check if username already exists
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        if c.fetchone():
            flash("Username already exists!", "error")
            conn.close()
            return redirect(url_for('signup'))

        # Insert new user if validations pass
        try:
            c.execute(
                'INSERT INTO users (email, username, password, question1, question2) VALUES (?, ?, ?, ?, ?)',
                (email, username, password, question1, question2)
            )
            conn.commit()
            flash('Sign up successful! You can now log in.', "success")
            return redirect(url_for('login'))
        except sqlite3.Error as e:
            flash(f'An error occurred: {str(e)}', "error")
        finally:
            conn.close()

    return render_template('signup.html')




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Connect to SQLite database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT password FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        # Check if user exists and password matches
        if user and password == user[0]:
            flash('Login successful!', "success")
            return redirect(url_for('index'))  # Redirect to the home page or dashboard
        else:
            flash('Invalid username or password.', "error")

    return render_template('login.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    # Clear image on a manual refresh (GET request without session flag)
    if request.method == 'GET' and not session.get('image_generated', False):
        session.pop('image_generated', None)
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part", "error")
            return redirect(url_for('index'))

        file = request.files['file']
        if file.filename == '':
            flash("No selected file", "error")
            return redirect(url_for('index'))

        if file:
            file.save(UPLOAD_IMAGE_PATH)
            subprocess.run([
                sys.executable, YOLO_DETECT_SCRIPT,
                '--weights', YOLO_WEIGHTS,
                '--source', UPLOAD_IMAGE_PATH,
                '--project', 'static',
                '--name', 'diagnosed_image',
                '--exist-ok'
            ])

            files = glob.glob("static/diagnosed_image/*.jpg")
            if files:
                latest_file = max(files, key=os.path.getctime)
                
                if os.path.exists(DETECTED_IMAGE_PATH):
                    os.remove(DETECTED_IMAGE_PATH)
                
                os.rename(latest_file, DETECTED_IMAGE_PATH)

            session['image_generated'] = True
            flash('Diagnosis completed!', "success")
            return redirect(url_for('results'))  # Redirect to results page

    return render_template('index.html')


@app.route('/forgot')
def forgot():
    return render_template('forgot.html')

@app.route('/resetPassword')
def resetPassword():
    return render_template('resetPassword.html')


# root for downloading report in pdf format 
@app.route('/download-report')
def download_report():
    # Define the path for the report PDF
    report_path = "static/diagnosed_image/dummy_report.pdf"
    
    # Generate the report if it doesn’t exist
    if not os.path.exists(report_path):
        generate_pdf_report(report_path)
    
    # Serve the PDF file for download
    return send_file(report_path, as_attachment=True, download_name="diagnosed_report.pdf")

def generate_pdf_report(path):
    """Function to generate a dummy PDF report."""
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter
    
    # Add some text to the PDF for the dummy report
    c.drawString(100, height - 100, "Detection Report")
    c.drawString(100, height - 150, "Patient Name: John Doe")
    c.drawString(100, height - 200, "Date of Diagnosis: 2023-10-25")
    c.drawString(100, height - 250, "Diagnosis Summary:")
    c.drawString(120, height - 300, "A fracture has been detected in the wrist region.")
    c.drawString(120, height - 350, "The detected fracture is located on the distal radius.")
    c.drawString(120, height - 400, "Recommendation: Consult with an orthopedic specialist.")

    # Save the PDF
    c.save()

    #handeling contact us section 

# creating feedback Table in database
@app.route('/create_feedback_table')
def create_feedback_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # SQL command to create the 'feedback' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    conn.commit()
    conn.close()
    return "Feedback table created successfully."

@app.route('/view_feedback')
def view_feedback():
    secret_key = request.args.get('key')
    
    # Check for a simple secret key (you can replace this with a more secure approach)
    if secret_key != 'admin321':
        return "Unauthorized access", 403

    # Query to fetch all feedback
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, message FROM feedback")
    feedback_list = cursor.fetchall()
    conn.close()

    return render_template('view_feedback.html', feedback=feedback_list)

@app.route('/results')
def results():
    # Check if the diagnosis image exists and session flag is set
    image_exists = os.path.exists(DETECTED_IMAGE_PATH) and session.get('image_generated', False)
    # Pass only the relative path within 'static' for the template
    return render_template('results.html', image_path='diagnosed_image/latest_detection.jpg' if image_exists else None)





if __name__ == '__main__':
    init_db()
    app.run(debug=True)
