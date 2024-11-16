from flask import Flask, request, render_template, flash, redirect, url_for
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

app = Flask(__name__)
app.secret_key = "your_secret_key"

GOOGLE_API_KEY = "AIzaSyAWZQ_VSR4xiOGLQMulMnSlAvLrCv5eTrs"

# Configure the LLM
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=GOOGLE_API_KEY)

@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        if file:
            # Save the uploaded image locally in static/uploads/
            file_path = f"static/uploads/{file.filename}"
            file.save(file_path)

            # Create a message with the image and prompt
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": ("I am providing a YOLO-evaluated image that contains detected class labels. "
             "Your task is to generate descriptions for each detected class based on the predefined mappings below.\n\n"
             "Detected Class Mappings:\n"
             "Bone anomaly: Bone anomaly detected, indicating potential structural irregularity.\n"
             "Bone lesion: Bone lesion detected; further evaluation may be needed to assess severity.\n"
             "Foreign body: Foreign body detected near bone structure, possibly requiring removal.\n"
             "Fracture: Bone fracture identified; urgent medical attention is advised.\n"
             "Metal: Metal implant detected, likely a post-surgical addition.\n"
             "Periosteal reaction: Periosteal reaction noted, often a sign of bone healing or infection.\n"
             "Pronator sign: Pronator sign visible, indicating possible skeletal irregularities.\n"
             "Soft tissue abnormality: Soft tissue swelling observed, possibly due to inflammation.\n"
             "No abnormalities: No abnormalities detected; this appears to be a normal X-ray. when you see anyother think write upload image again"),
                    },
                    # Update the image URL to be a fully qualified URL
                    {"type": "image_url", "image_url": f"http://127.0.0.1:5000/{file_path}"}
                ]
            )

            # Invoke the LLM
            try:
                response = llm.invoke([message])
                print("LLM Response:", response)  # Debug: Print the LLM response
                return render_template('result.html', report=response)  # Render the result.html template
            except Exception as e:
                flash(f"Error processing the image: {e}", 'error')
                return redirect(request.url)

    return render_template('upload.html')

@app.route('/result')
def result():
    return render_template('result.html')

if __name__ == '__main__':
    app.run(debug=True)
