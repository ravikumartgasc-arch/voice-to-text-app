import streamlit as st
import os
import time
import yt_dlp
from google import genai
from google.genai import types

# --- CONFIGURATION ---
# PASTE YOUR API KEY HERE
API_KEY = "AIzaSyBiJrO6riZ2Fhr85JVSEh0PQuzMrkBEhhw" 
MODEL_NAME = "gemini-flash-latest"

st.set_page_config(page_title="AI Transcriber", layout="centered")
st.title("🎙️ Universal AI Transcriber")

def get_client():
    return genai.Client(api_key=API_KEY)

def download_video(url):
    st.info(f"Attempting download from: {url}...")
    filename_base = "downloaded_media"

    # Cleanup old files
    for ext in ['.mp4', '.m4a', '.mp3', '.webm']:
        if os.path.exists(filename_base + ext):
            os.remove(filename_base + ext)

    # 1. Configure downloader for Facebook/YouTube
    ydl_opts = {
        'format': 'best', 
        'outtmpl': filename_base + '.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_filename = ydl.prepare_filename(info)

            # CRITICAL CHECK: Did it actually download?
            if not os.path.exists(final_filename) or os.path.getsize(final_filename) == 0:
                st.error("Download failed: File is empty or missing.")
                return None

            st.success(f"Downloaded: {final_filename}")
            return final_filename

    except Exception as e:
        st.error(f"Download Error: {str(e)}")
        return None

def transcribe(file_path):
    if not file_path or not os.path.exists(file_path):
        st.error("Error: No file to process.")
        return

    client = get_client()
    st.info("Uploading file to AI...")

    try:
        media_file = client.files.upload(file=file_path)

        with st.spinner("AI is processing (this takes 10-20s)..."):
            while media_file.state.name == "PROCESSING":
                time.sleep(2)
                media_file = client.files.get(name=media_file.name)

        if media_file.state.name == "FAILED":
            st.error("AI Processing Failed. The video format might be unsupported.")
            return

        st.success("Transcribing...")

        prompt = "Listen to the audio (English or any Indian language). Transcribe exactly as spoken in the native script."

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
            st.text_area("Result:", value=response.text, height=400)
            st.download_button("Download Text", response.text, file_name="transcription.txt")
        else:
            st.error("Empty response from AI.")

    except Exception as e:
        st.error(f"System Error: {e}")

# --- UI ---
tab1, tab2 = st.tabs(["🔗 Paste Link", "📂 Upload File"])

with tab1:
    url_input = st.text_input("Paste Facebook/YouTube Link:")
    if st.button("Transcribe Link"):
        if url_input:
            f = download_video(url_input)
            if f: transcribe(f)

with tab2:
    uploaded_file = st.file_uploader("Upload Audio/Video", type=['mp3', 'mp4', 'm4a', 'wav'])
    if uploaded_file and st.button("Transcribe File"):
        with open("temp_upload.mp4", "wb") as f:
            f.write(uploaded_file.getbuffer())
        transcribe("temp_upload.mp4")

