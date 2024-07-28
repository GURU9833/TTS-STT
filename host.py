import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os
from googletrans import Translator, LANGUAGES
from gtts import gTTS
import fitz  # PyMuPDF

# Initialize translator
translator = Translator()

def convert_speech_to_text(audio_path):
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(audio_path)
    with audio_file as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        text = "Google Speech Recognition could not understand the audio."
    except sr.RequestError as e:
        text = f"Could not request results from Google Speech Recognition service; {e}"
    return text

def translate_text(text, dest_language):
    try:
        translated = translator.translate(text, dest=dest_language)
        return translated.text
    except Exception as e:
        return f"Translation error: {e}"

def text_to_speech(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
            tts.save(temp_audio_file.name)
            return temp_audio_file.name
    except Exception as e:
        return f"Text to Speech error: {e}"

def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# Convert language codes to full names for display
language_choices = {full_name.capitalize(): lang_code for lang_code, full_name in LANGUAGES.items()}

st.title("Speech to Text and Text to Speech with Translation")

# Speech to Text Section
st.header("MP3 to Text Converter with Translation")
st.write("Upload an MP3 file, and this app will convert the speech to text and translate it.")

uploaded_file = st.file_uploader("Choose an MP3 file", type=["mp3"])

languages = {
    "Afrikaans": "af",
    "Arabic": "ar",
    "Chinese (Simplified)": "zh-cn",
    "Chinese (Traditional)": "zh-tw",
    "Dutch": "nl",
    "English": "en",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Italian": "it",
    "Japanese": "ja",
    "Korean": "ko",
    "Portuguese": "pt",
    "Russian": "ru",
    "Spanish": "es",
    "Swedish": "sv"
}

dest_language = st.selectbox("Select language for translation", list(languages.keys()))

if uploaded_file is not None:
    file_details = {
        "filename": uploaded_file.name,
        "filetype": uploaded_file.type,
        "filesize": uploaded_file.size
    }
    st.write(file_details)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_file_path = temp_file.name

        st.audio(temp_file_path)
        audio = AudioSegment.from_mp3(temp_file_path)
        temp_wav_path = os.path.join(tempfile.gettempdir(), 'temp_audio.wav')
        audio.export(temp_wav_path, format="wav")
        text = convert_speech_to_text(temp_wav_path)
        st.write("Transcribed Text:")
        st.text_area("Output Text", text)
        translated_text = translate_text(text, languages[dest_language])
        st.write(f"Translated Text ({dest_language}):")
        st.text_area("Translated Output", translated_text)

    except Exception as e:
        st.error(f"Error processing file: {e}")

    finally:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

# Text to Speech Section
st.header("Text to Speech and Translation")

text_option = st.radio("Select input type:", ("Text", "PDF File"))

if text_option == "Text":
    text = st.text_area("Enter text here:")
else:
    uploaded_pdf = st.file_uploader("Upload a PDF file", type=["pdf"])
    if uploaded_pdf is not None:
        text = extract_text_from_pdf(uploaded_pdf)
        st.text_area("Extracted Text from PDF", value=text, height=200)

target_language = st.selectbox("Select target language for translation", options=list(language_choices.keys()))

if st.button("Translate and Convert to Speech"):
    if text_option == "Text" and not text:
        st.error("Please enter some text.")
    elif text_option == "PDF File" and uploaded_pdf is None:
        st.error("Please upload a PDF file.")
    else:
        lang_code = language_choices[target_language]
        translated_text = translate_text(text, lang_code)
        st.text_area("Translated Text", value=translated_text, height=200)
        
        if not translated_text.startswith("Translation error"):
            audio_file = text_to_speech(translated_text, lang=lang_code)
            if not audio_file.startswith("Text to Speech error"):
                audio_bytes = open(audio_file, "rb").read()
                st.audio(audio_bytes, format="audio/mp3")
                os.remove(audio_file)
            else:
                st.error(audio_file)
