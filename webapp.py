import streamlit as st
import os
import time
import yt_dlp
import google.generativeai as genai

# --- CONFIGURATION ---
# PASTE YOUR API KEY HERE
API_KEY = "AIzaSyBiJrO6riZ2Fhr85JVSEh0PQuzMrkBEhhw"

# Configure the Stable Library
genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Universal Transcriber", layout="centered")
st.title("🎙️ AI Transcriber (Stable Version)")

# --- 1. TEST API KEY ON START ---
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    # Quick test to see if Key works
    response = model.generate_content("Hello")
except Exception as e:
    st.error(f"❌ API Key Error: Please check your API Key. Details: {e}")
    st.stop()

# --- 2. DOWNLOADER FUNCTION ---
def download_video(url):
    st.info(f"⏳ Connecting to: {url}...")
    filename_base = "downloaded_media"
    
    # Clean up old files
    for ext in ['.mp4', '.m4a', '.mp3', '.webm']:
        if os.path.exists(filename_base + ext):
            os.remove(filename_base + ext)

    # Browser Masquerade Options
    ydl_opts = {
        'format': 'best',
        'outtmpl': filename_base + '.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            final_filename = ydl.prepare_filename(info)
            
            # Check if file actually exists and has size
            if not os.path.exists(final_filename) or os.path.getsize(final_filename) == 0:
                st.error("❌ Download failed: File is empty.")
                return None
            
            st.success(f"✅ Downloaded: {final_filename}")
            return final_filename

    except Exception as e:
        st.error(f"❌ Download Error: {e}")
        if "facebook" in url:
            st.warning("💡 Facebook Hint: Facebook blocks servers often. Please download the video manually on your phone/PC, then use the 'Upload File' tab.")
        return None

# --- 3. TRANSCRIBE FUNCTION (STABLE) ---
def transcribe_media(file_path):
    if not os.path.exists(file_path):
        st.error("❌ Error: File not found.")
        return

    # Check file size
    file_size = os.path.getsize(file_path) / (1024 * 1024) # Size in MB
    st.write(f"📄 File Size: {file_size:.2f} MB")
    
    try:
        st.info("🚀 Uploading to Gemini (this may take time)...")
        # Upload using the Stable V1 API
        video_file = genai.upload_file(path=file_path)
        
        # Wait for processing
        with st.spinner("⏳ AI is processing the video..."):
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            st.error("❌ AI Processing Failed. The video format might be unsupported.")
            return

        st.success("✅ Ready! Transcribing now...")
        
        # Transcribe
        prompt = "Listen to the audio. Transcribe it exactly as spoken (Verbatim) in the native script (English/Indian Languages). Do not translate."
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content([video_file, prompt])
        
        if response.text:
            st.subheader("📝 Transcription:")
            st.text_area("Result", value=response.text, height=400)
            st.download_button("Download Text", response.text, file_name="transcription.txt")
        else:
            st.warning("⚠️ The AI returned empty text. (Audio might be silent?)")

    except Exception as e:
        st.error(f"❌ System Error: {e}")

# --- UI TABS ---
tab1, tab2 = st.tabs(["🔗 Paste Link", "📂 Upload File"])

with tab1:
    url = st.text_input("Paste Link (YouTube/Facebook):")
    if st.button("Transcribe Link"):
        if url:
            f = download_video(url)
            if f: transcribe_media(f)

with tab2:
    uploaded = st.file_uploader("Upload Audio/Video", type=['mp3', 'mp4', 'wav', 'm4a'])
    if uploaded and st.button("Transcribe Upload"):
        # Save temp file
        with open("temp_upload.mp4", "wb") as f:
            f.write(uploaded.getbuffer())
        transcribe_media("temp_upload.mp4")
