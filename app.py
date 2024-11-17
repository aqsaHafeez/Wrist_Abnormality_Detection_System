from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
import sqlite3
import os
import subprocess
import sys
import glob
import logging
from flask import Flask, send_file, session
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from flask_sqlalchemy import SQLAlchemy
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import textwrap
from flask import send_file, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

GOOGLE_API_KEY = "AIzaSyAWZQ_VSR4xiOGLQMulMnSlAvLrCv5eTrs"
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=GOOGLE_API_KEY)

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
DETECTED_IMAGE_PATH = os.path.join('static', 'diagnosed_image', 'latest_detection.jpg').replace("\\", "/")
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

def check_security_questions(username, answer1, answer2):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Query user data based on username
    c.execute('SELECT question1, question2 FROM users WHERE username = ?', (username,))
    user = c.fetchone()

    conn.close()

    if user:
        stored_answer1, stored_answer2 = user
        return answer1 == stored_answer1 and answer2 == stored_answer2
    return False


@app.route('/reset-password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Validate that new passwords match
        if new_password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('reset_password', username=username))
        
        # Password validation: length >= 8, contains at least one letter and one number
        if len(new_password) < 8 or not re.search(r'[A-Za-z]', new_password) or not re.search(r'[0-9]', new_password):
            flash("Password must be at least 8 characters long and contain both letters and numbers!", "error")
            return redirect(url_for('reset_password', username=username))

        # Update the password in the database
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()

            # Check if username exists
            c.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = c.fetchone()

            if user:
                # Update the user's password in the database
                c.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, username))
                conn.commit()
                flash("Password successfully updated!", "success")
                return redirect(url_for('login'))  # Redirect to login page after successful reset
            else:
                flash("User not found!", "error")
        except sqlite3.Error as e:
            flash(f"An error occurred: {e}", "error")
        finally:
            conn.close()

    return render_template('resetPassword.html', username=username)


@app.route('/forgot')
def forgot():
    return render_template('forgot.html')

    

@app.route('/submit-reset-request', methods=['POST'])
def submit_reset_request():
    username = request.form['username']
    question1_answer = request.form['question1']
    question2_answer = request.form['question2']

    # Check the answers against the database
    if check_security_questions(username, question1_answer, question2_answer):
        # Redirect to reset_password, passing the username in the URL
        return redirect(url_for('reset_password', username=username))
    else:
        flash("Incorrect answers to the security questions. Please try again.", 'error')
        return redirect(url_for('forgot'))


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
            session['username'] = username  # Set the session variable
            flash('Login successful!', 'success')
            return redirect(url_for('index'))  # Redirect to home page or dashboard
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/index', methods=['GET', 'POST'])
def index():
    # Clear session flag on refresh (GET request)
    if request.method == 'GET' and not session.get('image_generated', False):
        session.pop('image_generated', None)
        session.pop('generated_report', None)  # Clear report data on refresh

    if request.method == 'POST':
        # Capture form data
        session['patient_name'] = request.form.get('name', 'Unknown')
        session['patient_age'] = request.form.get('age', 'Unknown')
        session['patient_gender'] = request.form.get('gender', 'Unknown')
        session['wrist_side'] = request.form.get('wrist', 'Unknown')

        # Debugging: Print the form data
        print("Form Data Captured:")
        print(f"Name: {session['patient_name']}")
        print(f"Age: {session['patient_age']}")
        print(f"Gender: {session['patient_gender']}")
        print(f"Wrist Side: {session['wrist_side']}")

        if 'file' not in request.files:
            flash("No file part", "error")
            return redirect(url_for('index'))

        file = request.files['file']
        if file.filename == '':
            flash("No selected file", "error")
            return redirect(url_for('index'))

        if file:
            # Save the uploaded file and perform YOLO analysis
            file.save(UPLOAD_IMAGE_PATH)
            subprocess.run([
                sys.executable, YOLO_DETECT_SCRIPT,
                '--weights', YOLO_WEIGHTS,
                '--source', UPLOAD_IMAGE_PATH,
                '--project', 'static',
                '--name', 'diagnosed_image',
                '--exist-ok'
            ])

            # Move the latest detected image
            files = glob.glob("static/diagnosed_image/*.jpg")
            if files:
                latest_file = max(files, key=os.path.getctime)
                if os.path.exists(DETECTED_IMAGE_PATH):
                    os.remove(DETECTED_IMAGE_PATH)
                os.rename(latest_file, DETECTED_IMAGE_PATH)

            # Generate report using Gemini LLM
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": (
                            "I am providing a YOLO-evaluated image that contains detected class labels. "
                            "Your task is to generate descriptions for each detected class based on the predefined mappings below.if you find two same types of fracture labels then tell that there are two but ont repeat the advice. \n\n"
                            "Detected Class Mappings:\n"
                            "Bone anomaly: Bone anomaly detected, indicating potential structural irregularity.\n"
                            "Bone lesion: Bone lesion detected; further evaluation may be needed to assess severity.\n"
                            "Foreign body: Foreign body detected near bone structure, possibly requiring removal.\n"
                            "Fracture: Bone fracture identified; urgent medical attention is advised.\n"
                            "Metal: Metal implant detected, likely a post-surgical addition.\n"
                            "Periosteal reaction: Periosteal reaction noted, often a sign of bone healing or infection.\n"
                            "Pronator sign: Pronator sign visible, indicating possible skeletal irregularities.\n"
                            "Soft tissue abnormality: Soft tissue swelling observed, possibly due to inflammation.\n"
                            "No abnormalities: No abnormalities detected; this appears to be a normal X-ray."
                        ),
                    },
                    {"type": "image_url", "image_url": f"http://127.0.0.1:5000/{DETECTED_IMAGE_PATH}"}
                ]
            )
            try:
                response = llm.invoke([message])
                if response and hasattr(response, 'content'):
                    session['generated_report'] = response.content
                    print("Gemini Response:", response.content)  # Debugging
                else:
                    session['generated_report'] = "No valid response received from Gemini."
                    print("Gemini Response is empty or invalid.")
            except Exception as e:
                flash(f"Error generating report: {e}", "error")
                session['generated_report'] = f"Error: {e}"

            # Mark session as analysis completed
            session['image_generated'] = True
            flash('Diagnosis and report generation completed!', "success")
            return redirect(url_for('results'))  # Redirect to the results page

    return render_template('index.html')



@app.route('/logout')
def logout():
    # Clear the session to log the user out
    session.clear()  # You can replace 'username' with any session data key you're using
    
    # Clear any flash messages that might have been carried over from previous requests
    flash("You have been logged out successfully!", "success")
    
    # Redirect to the login page
    return redirect(url_for('login'))



# root for downloading report in pdf format 
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from datetime import datetime
import textwrap

@app.route('/download-report')
def download_report():
    # Define the path for the report PDF
    report_path = "static/diagnosed_image/detailed_report.pdf"
    
    # Retrieve form data and Gemini response from the session
    patient_name = session.get('patient_name', 'Unknown')
    patient_age = session.get('patient_age', 'Unknown')
    patient_gender = session.get('patient_gender', 'Unknown')
    wrist_side = session.get('wrist_side', 'Unknown')
    gemini_response = session.get('generated_report', 'No diagnosis report available.')

    # Debugging: Log data retrieved from session
    print(f"Generating report with the following data:\n"
          f"Name: {patient_name}, Age: {patient_age}, Gender: {patient_gender}, "
          f"Wrist: {wrist_side}, Diagnosis: {gemini_response}")
    
    # Generate the detailed PDF report
    generate_pdf_report(
        path=report_path,
        name=patient_name,
        age=patient_age,
        gender=patient_gender,
        wrist=wrist_side,
        diagnosis_summary=gemini_response
    )
    
    # Serve the PDF file for download
    return send_file(report_path, as_attachment=True, download_name="detailed_report.pdf")


def generate_pdf_report(path, name, age, gender, wrist, diagnosis_summary):
    """Function to generate a detailed PDF report."""
    c = canvas.Canvas(path, pagesize=letter)
    width, height = letter

    # Define colors
    header_color = colors.HexColor("#3498db")  # Soft Blue for header
    section_bg_color = colors.HexColor("#ecf0f1")  # Light grey background for sections
    text_color = colors.black  # Default text color
    border_color = colors.HexColor("#2980b9")  # Blue border color
    title_color = colors.HexColor("#2c3e50")  # Dark color for titles

    # Add system name at the top-left of the document
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(header_color)
    c.drawString(20, height - 30, "Wrist Abnormality Detection System")

    # Add current date and time at the top-right of the document
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.setFillColor(text_color)
    c.drawRightString(width - 20, height - 30, current_time)

    # Add space at the top (2 lines of space)
    vertical_offset = 150

    # Add report header with a border
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(header_color)
    c.drawString(100, height - 50, "X-ray Analysis Report")
    
    # Add a thin line below the title
    c.setFillColor(border_color)
    c.line(100, height - 55, width - 100, height - 55)

    # Adjust spacing for patient details (top-to-bottom order)
    details_start_y = height - 100  # Starting Y-coordinate for the patient details section

    c.setFont("Helvetica", 12)
    c.setFillColor(title_color)

    # Add Patient details one by one from top to bottom
    c.drawString(110, details_start_y, f"Patient Name: {name}")
    c.drawString(110, details_start_y - 20, f"Age: {age}")
    c.drawString(110, details_start_y - 40, f"Gender: {gender}")
    c.drawString(110, details_start_y - 60, f"Wrist Side Analyzed: {wrist}")

    # Draw a separator line after the patient details
    c.setFillColor(border_color)
    c.line(100, details_start_y - 80, width - 100, details_start_y - 80)


    # Add diagnosis summary header
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(title_color)
    c.drawString(100, details_start_y - 100, "Diagnosis Summary:")

    # Add diagnosis summary text with wrapping and padding
    text = c.beginText(100, details_start_y - 120)
    text.setFont("Helvetica", 12)
    text.setLeading(14)  # Line spacing for better readability
    text.setFillColor(text_color)

    # Wrap the text to fit within the page width (400px)
    diagnosis_summary = diagnosis_summary or "No diagnosis summary provided."
    wrapped_lines = textwrap.wrap(diagnosis_summary, width=80)  # Adjust width as needed
    for line in wrapped_lines:
        text.textLine(line)

    c.drawText(text)

    # Add a footer with page number
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(text_color)
    c.drawRightString(width - 20, 20, f"Page 1")

    # Save the PDF
    c.save()



@app.route('/results')
def results():
    # Check if the analysis is completed
    if not session.get('image_generated', False):
        flash("No analysis found. Please upload an image first.", "error")
        return redirect(url_for('index'))

    # Retrieve the YOLO-detected image and generated report
    image_path = 'diagnosed_image/latest_detection.jpg' if session.get('image_generated', False) else None
    report_content = session.get('generated_report', "Report content not available.")

    # Render the results page
    return render_template('results.html', image_path=image_path, report=report_content)



if __name__ == '__main__':
    init_db()
    app.run(debug=True)
