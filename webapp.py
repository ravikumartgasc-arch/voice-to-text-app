import streamlit as st
import os
import time
import yt_dlp
from google import genai
from google.genai import types

# --- CONFIGURATION ---
# PASTE YOUR API KEY HERE
API_KEY = "AIzaSyBiJrO6riZ2Fhr85JVSEh0PQuzMrkBEhhw"

# 1. SETUP CLIENT
try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"❌ Client Error: {e}")
    st.stop()

st.set_page_config(page_title="Universal AI Transcriber", layout="centered")
st.title("🎙️ Universal AI Transcriber")
st.caption("Mode: iOS Emulation (Bypasses 403 Errors)")

# --- 2. DOWNLOADER (The "iPhone" Fix) ---
def download_audio(url):
    st.info(f"⏳ Connecting to: {url}...")
    filename_base = "downloaded_audio"
    
    # Cleanup
    for ext in ['.mp3', '.m4a', '.wav', '.webm']:
        if os.path.exists(filename_base + ext):
            os.remove(filename_base + ext)

    # TRICK: Pretend to be an iPhone App
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': filename_base + '.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        # This argument forces YouTube to treat us like a Mobile App
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android'],
            }
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_filename = "downloaded_audio.mp3"
            
            if not os.path.exists(final_filename) or os.path.getsize(final_filename) == 0:
                st.error("❌ Download failed. Server blocked.")
                return None
            
            st.success(f"✅ Audio Downloaded!")
            return final_filename
    except Exception as e:
        st.error(f"❌ Download Error: {e}")
        return None

# --- 3. TRANSCRIBE ---
def transcribe_media(file_path):
    if not os.path.exists(file_path):
        st.error("❌ File not found.")
        return

    st.write(f"📄 Processing file...")

    try:
        st.info("🚀 Uploading to Gemini...")
        video_file = client.files.upload(file=file_path)
        
        with st.spinner("⏳ AI is processing..."):
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = client.files.get(name=video_file.name)

        if video_file.state.name == "FAILED":
            st.error(f"❌ Processing Failed.")
            return

        st.success("✅ Transcribing...")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[video_file, "Transcribe this audio exactly as spoken (Verbatim). Do not translate. Identify the language."]
        )
        
        if response.text:
            st.text_area("Result:", value=response.text, height=400)
            st.download_button("Download Text", response.text, file_name="transcription.txt")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# --- UI ---
tab1, tab2 = st.tabs(["🔗 YouTube Link", "📂 Upload File"])

with tab1:
    url = st.text_input("Paste Link:")
    if st.button("Transcribe Link"):
        if url:
            f = download_audio(url)
            if f: transcribe_media(f)

with tab2:
    uploaded = st.file_uploader("Upload File", type=['mp3', 'mp4', 'wav', 'm4a'])
    if uploaded and st.button("Transcribe Upload"):
        ext = os.path.splitext(uploaded.name)[1]
        save_path = f"temp_upload{ext}"
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        transcribe_media(save_path)
