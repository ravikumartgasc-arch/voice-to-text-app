import streamlit as st
import os
import yt_dlp
from google import genai
from google.genai import types

# --- CONFIGURATION ---
API_KEY = "AIzaSyBiJrO6riZ2Fhr85JVSEh0PQuzMrkBEhhw"
MODEL_NAME = "gemini-flash-latest"

# Set page title
st.set_page_config(page_title="AI Transcriber", layout="centered")

st.title("🎙️ AI Voice to Text")
st.write("Upload a file or paste a link (YouTube/Facebook/etc).")

def get_client():
    return genai.Client(api_key=API_KEY)

def download_video(url):
    st.info(f"Downloading from: {url}...")
    filename_base = "downloaded_media"
    ydl_opts = {
        'format': 'best',
        'outtmpl': filename_base + '.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        # We assume the host machine has FFmpeg installed
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        st.error(f"Download Failed: {e}")
        return None

def transcribe(file_path):
    if not file_path: return
    
    client = get_client()
    st.info("Uploading to Google AI...")
    
    try:
        media_file = client.files.upload(file=file_path)
        
        with st.spinner("Processing (this may take a moment)..."):
            import time
            while media_file.state.name == "PROCESSING":
                time.sleep(2)
                media_file = client.files.get(name=media_file.name)

        if media_file.state.name == "FAILED":
            st.error("Processing failed.")
            return

        st.success("Transcribing...")
        prompt = "Listen to the speech (English/Indian languages). Transcribe exactly as spoken in native script."
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[media_file, prompt],
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE")
                ]
            )
        )
        
        if response.text:
            st.text_area("Result:", value=response.text, height=300)
            st.download_button("Download Text", response.text, file_name="transcription.txt")
        else:
            st.error("Empty response.")

    except Exception as e:
        st.error(f"Error: {e}")

# --- UI TABS ---
tab1, tab2 = st.tabs(["🔗 From Link", "📂 From File"])

with tab1:
    url = st.text_input("Paste Link (YouTube/Facebook):")
    if st.button("Transcribe Link"):
        if url:
            f = download_video(url)
            if f: transcribe(f)

with tab2:
    uploaded_file = st.file_uploader("Upload Audio/Video", type=['mp3', 'mp4', 'wav', 'm4a'])
    if uploaded_file:
        # Save uploaded file temporarily
        with open("temp_upload.mp4", "wb") as f:
            f.write(uploaded_file.getbuffer())
        if st.button("Transcribe File"):
            transcribe("temp_upload.mp4")