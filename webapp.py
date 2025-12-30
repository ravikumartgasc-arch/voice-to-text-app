import streamlit as st
import os
import time
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

st.set_page_config(page_title="AI Transcriber", layout="centered")
st.title("🎙️ AI Transcriber (Upload Only)")
st.caption("Powered by Gemini 2.5 Flash • Works with Audio & Video")

# --- TRANSCRIBE FUNCTION ---
def transcribe_media(file_path):
    if not os.path.exists(file_path):
        st.error("❌ File not found.")
        return

    st.info(f"📄 Processing file: `{os.path.basename(file_path)}`")

    try:
        st.info("🚀 Uploading to Gemini...")
        
        # Upload file to Google
        video_file = client.files.upload(file=file_path)
        
        # Wait for processing
        with st.spinner("⏳ AI is listening and processing..."):
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = client.files.get(name=video_file.name)

        if video_file.state.name == "FAILED":
            st.error(f"❌ Processing Failed. The file format might be corrupted.")
            return

        st.success("✅ Transcribing...")
        
        # Generate Transcription
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                video_file,
                "Transcribe this audio exactly as spoken (Verbatim). Do not translate. Identify the language at the start."
            ]
        )
        
        if response.text:
            st.divider()
            st.subheader("📝 Result:")
            st.text_area("Transcription:", value=response.text, height=500)
            st.download_button("Download Text File", response.text, file_name="transcription.txt")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# --- UI ---
st.write("### Upload your file")
st.write("Supported: MP3, WAV, M4A, MP4 (Max 200MB)")

uploaded_file = st.file_uploader("Drag and drop here", type=['mp3', 'mp4', 'wav', 'm4a', 'mpeg', 'webm', 'ogg'])

if uploaded_file is not None:
    if st.button("Start Transcription"):
        # Save the uploaded file temporarily
        ext = os.path.splitext(uploaded_file.name)[1]
        if not ext: ext = ".mp4" # Default fallback
        
        save_path = f"temp_upload{ext}"
        
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        transcribe_media(save_path)
