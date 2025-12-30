import streamlit as st
import os
import time
import yt_dlp
import google.generativeai as genai

# --- CONFIGURATION ---
# PASTE YOUR API KEY INSIDE THE QUOTES BELOW
API_KEY = "AIzaSyBiJrO6riZ2Fhr85JVSEh0PQuzMrkBEhhw"

# Configure the Google AI Library
genai.configure(api_key=API_KEY)

# Page Setup
st.set_page_config(page_title="Universal AI Transcriber", layout="centered")
st.title("🎙️ Universal AI Transcriber")
st.caption("Supports: YouTube, Facebook, Uploads (English & Indian Languages)")

# --- 1. SYSTEM CHECK ON STARTUP ---
# We test if the API key works immediately to warn you if it's wrong.
try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    # Simple handshake to verify connection
except Exception as e:
    st.error(f"❌ API Key Error: Please check your API Key in the code.\n\nDetails: {e}")
    st.stop()

# --- 2. DOWNLOADER FUNCTION ---
def download_video(url):
    st.info(f"⏳ Connecting to: {url}...")
    filename_base = "downloaded_media"
    
    # Clean up old files to prevent errors
    for ext in ['.mp4', '.m4a', '.mp3', '.webm']:
        if os.path.exists(filename_base + ext):
            os.remove(filename_base + ext)

    # Configure the downloader to look like a real browser (Tricks Facebook)
    ydl_opts = {
        'format': 'best', # Safer than asking for specific audio
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
            
            # CRITICAL CHECK: Did the file actually save?
            if not os.path.exists(final_filename) or os.path.getsize(final_filename) == 0:
                st.error("❌ Download failed: The file is empty or missing.")
                return None
            
            st.success(f"✅ Download successful: {final_filename}")
            return final_filename

    except Exception as e:
        st.error(f"❌ Download Error: {e}")
        if "facebook" in url:
            st.warning("💡 Hint for Facebook: If the download fails, Facebook might be blocking the server. Please download the video manually to your phone/PC and use the 'Upload File' tab instead.")
        return None

# --- 3. TRANSCRIBE FUNCTION ---
def transcribe_media(file_path):
    if not os.path.exists(file_path):
        st.error("❌ Error: File not found.")
        return

    # Check file size (Max 2GB is Google's limit, but we check for 0 bytes)
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    st.write(f"📄 File Size: {file_size_mb:.2f} MB")
    
    if file_size_mb < 0.001:
        st.error("❌ Error: File is empty.")
        return

    try:
        st.info("🚀 Uploading to Google AI (Videos take 10-30s)...")
        
        # Upload the file
        video_file = genai.upload_file(path=file_path)
        
        # Wait for Google to process it
        with st.spinner("⏳ AI is processing the media..."):
            while video_file.state.name == "PROCESSING":
                time.sleep(2)
                video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            st.error("❌ AI Processing Failed. The format might be unsupported.")
            return

        st.success("✅ Ready! Generating transcription...")
        
        # The Instruction Prompt
        prompt = """
        You are an expert multilingual transcriber.
        Listen to the speech in this media. It may be in English or any Indian language (Telugu, Tamil, Kannada, Hindi, etc.).
        
        Your Goal:
        1. Identify the language.
        2. Transcribe the speech EXACTLY as spoken (Verbatim).
        3. Use the native script for that language (e.g. write Telugu in Telugu script).
        4. Do not translate.
        """
        
        # Generate Content
        response = model.generate_content([video_file, prompt])
        
        if response.text:
            st.subheader("📝 Transcription Result:")
            st.text_area("Copy your text below:", value=response.text, height=400)
            st.download_button("Download as Text File", response.text, file_name="transcription.txt")
        else:
            st.warning("⚠️ The AI returned empty text. (The audio might be silent or unclear).")

    except Exception as e:
        st.error(f"❌ System Error: {e}")

# --- UI TABS ---
tab1, tab2 = st.tabs(["🔗 Paste Link", "📂 Upload File"])

# TAB 1: Link Handling
with tab1:
    url_input = st.text_input("Paste Facebook/YouTube Link:")
    if st.button("Transcribe Link"):
        if url_input:
            downloaded_file = download_video(url_input)
            if downloaded_file:
                transcribe_media(downloaded_file)
        else:
            st.warning("Please paste a link first.")

# TAB 2: File Upload Handling
with tab2:
    uploaded_file = st.file_uploader("Upload Audio or Video", type=['mp3', 'mp4', 'wav', 'm4a', 'mpeg', 'webm'])
    if uploaded_file and st.button("Transcribe Uploaded File"):
        # We must save the uploaded file to disk first
        with open("temp_upload.mp4", "wb") as f:
            f.write(uploaded_file.getbuffer())
        transcribe_media("temp_upload.mp4")
