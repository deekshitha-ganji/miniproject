from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from functools import wraps
import speech_recognition as sr
from googletrans import Translator
import nltk
from nltk.tokenize import word_tokenize
import os
from dotenv import load_dotenv
import google.generativeai as genai
from gtts import gTTS


# Load environment variables from .env file
load_dotenv()

# Configure the generative AI model
genai.configure(api_key=os.getenv("GfjnvK"))
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

def clean_response_text(response_text):
    # Remove asterisks and replace them with appropriate HTML tags for bold and italics
    cleaned_text = response_text.replace("**", "<b>").replace("*", "<i>").replace("</i><b>", "</b>").replace("<i>", "").replace("</i>", "").replace("<b>", "").replace("</b>", "")
    return cleaned_text

def get_gemini_response(question):
    response = chat.send_message(question + " Suggest some remedies", stream=True)
    response_text = [chunk.text for chunk in response]
    cleaned_response = [clean_response_text(text) for text in response_text]
    return cleaned_response

app = Flask(__name__)
app.secret_key = 'supersecretkey'


# Dummy user data (in a real app, use a database)
users = {
    "user": "password"
}

# Custom Telugu stopwords list
telugu_stopwords = {'ఇది', 'అది', 'నేను', 'మా', 'మీ', 'ఎలా', 'ఏమి', 'ఎక్కడ', 'ఎప్పుడు', 'ఎందుకు', 'ఎలా', 'కాదు', 'వుంది', 'ఉంది', 'లేదు'}

# Function to extract keywords
def extract_keywords(text):
    words = word_tokenize(text.lower())
    words = [word for word in words if word.isalnum() and word not in telugu_stopwords]
    return list(set(words))  # Removing duplicates

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/start')
def start():
    session['logged_in'] = True
    return redirect(url_for('main'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('signup'))
        users[username] = password
        flash('Registration successful. Please login.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/main')
@login_required
def main():
    return render_template('index.html')

@app.route('/record')
@login_required
def record():
    recognizer = sr.Recognizer()
    translator = Translator()

    with sr.Microphone() as source:
        print("మాట్లాడు")  # "Talk" in Telugu
        audio_text = recognizer.listen(source)
        print("సమయం ముగిసింది, ధన్యవాదాలు")  # "Time over, thanks" in Telugu

        try:
            # Recognize the speech in Telugu
            telugu_text = recognizer.recognize_google(audio_text, language='te-IN')
            print("పాఠ్యం: " + telugu_text)  # "Text:" in Telugu

            # Translate Telugu text to English
            translated_text = translator.translate(telugu_text, src='te', dest='en').text
            print("Translated Text: " + translated_text)  # "Translated Text:" in English

            # Download necessary NLTK data files
            nltk.download('punkt')

            # Extract and print keywords
            keywords = extract_keywords(translated_text)
            print("Keywords:", keywords)  # "Keywords:" in English

            # Get response from Gemini Generative AI
            response = get_gemini_response(translated_text)
            print("AI Response:", response)  # "AI Response:" in English

            # Convert the response to Telugu
            response_text_telugu = translator.translate(' '.join(response), src='en', dest='te').text

            # Generate speech from the AI response in Telugu
            tts = gTTS(response_text_telugu, lang='te')
            audio_file = "response.mp3"
            tts.save(audio_file)

            return render_template('index.html', text=telugu_text, translated_text=translated_text, keywords=keywords, response=response, audio_file=audio_file)

        except Exception as e:
            print("క్షమించాలి, అర్థం కాలేదు")  # "Sorry, I did not get that" in Telugu
            print(e)
            return render_template('index.html', text="క్షమించాలి, అర్థం కాలేదు", translated_text="", keywords="", response="")

@app.route('/play_audio')
@login_required
def play_audio():
    audio_file = request.args.get('audio_file', default='response.mp3', type=str)
    return send_file(audio_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
