import streamlit as st
import os
import time
import yt_dlp
import google.generativeai as genai

# --- CONFIGURATION ---
# PASTE YOUR API KEY HERE
API_KEY = "AIzaSyBiJrO6riZ2Fhr85JVSEh0PQuzMrkBEhhw"

genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Universal AI Transcriber", layout="centered")
st.title("🎙️ Universal AI Transcriber")

# --- 1. DOWNLOADER (Force MP4 for Safety) ---
def download_video(url):
    st.info(f"⏳ Connecting to: {url}...")
    filename_base = "downloaded_media"
    
    # Cleanup
    for ext in ['.mp4', '.m4a', '.mp3', '.webm', '.mkv']:
        if os.path.exists(filename_base + ext):
            os.remove(filename_base + ext)

    # We force 'ext=mp4' so Google AI definitely accepts it
    ydl_opts = {
        'format': 'best[ext=mp4]/best', 
        'outtmpl': filename_base + '.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_filename = ydl.prepare_filename(info)
            
            if not os.path.exists(final_filename) or os.path.getsize(final_filename) == 0:
                st.error("❌ Download failed: File empty.")
                return None
            
            st.success(f"✅ Downloaded: {final_filename}")
            return final_filename

    except Exception as e:
        st.error(f"❌ Download Error: {e}")
        return None

# --- 2. TRANSCRIBE (With MIME-TYPE Fix) ---
def transcribe_media(file_path):
    if not os.path.exists(file_path):
        st.error("❌ File not found.")
        return

    # Determine the correct MIME type so Google doesn't reject it
    mime_type = "video/mp4" # Default to video
    if file_path.lower().endswith(".mp3"):
        mime_type = "audio/mp3"
    elif file_path.lower().endswith(".wav"):
        mime_type = "audio/wav"
    elif file_path.lower().endswith(".m4a"):
        mime_type = "audio/mp4"
    elif file_path.lower().endswith(".ogg"):
        mime_type = "audio/ogg"
        
    st.write(f"📄 Processing as: `{mime_type}`")

    try:
        st.info("🚀 Uploading to Gemini...")
        
        # --- THE FIX: We explicitly pass 'mime_type' here ---
        video_file = genai.upload_file(path=file_path, mime_type=mime_type)
        
        with st.spinner("⏳ AI is processing (this takes 10-30s)..."):
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            st.error(f"❌ AI Processing Failed. Google rejected the file format.\nDetails: {video_file}")
            return

        st.success("✅ Transcribing...")
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = "Transcribe this audio exactly as spoken (Verbatim). Do not translate. Identify the language (English/Indian) and write in native script."
        
        response = model.generate_content([video_file, prompt])
        
        if response.text:
            st.text_area("Result:", value=response.text, height=400)
            st.download_button("Download Text", response.text, file_name="transcription.txt")
        else:
            st.warning("⚠️ Empty response from AI.")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# --- UI ---
tab1, tab2 = st.tabs(["🔗 Link", "📂 Upload"])

with tab1:
    url = st.text_input("Paste Link:")
    if st.button("Transcribe Link"):
        if url:
            f = download_video(url)
            if f: transcribe_media(f)

with tab2:
    uploaded = st.file_uploader("Upload File", type=['mp3', 'mp4', 'wav', 'm4a'])
    if uploaded and st.button("Transcribe Upload"):
        # Save with correct extension
        ext = os.path.splitext(uploaded.name)[1]
        save_path = f"temp_upload{ext}"
        with open(save_path, "wb") as f:
            f.write(uploaded.getbuffer())
        transcribe_media(save_path)
